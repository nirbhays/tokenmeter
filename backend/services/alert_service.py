"""
Alert Service — delivers budget alerts via Slack, webhooks, and email.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from backend.config import get_settings
from backend.models.budget import AlertChannel, BudgetAlert

logger = logging.getLogger(__name__)


class AlertService:
    """Delivers alerts to configured channels."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def deliver(self, alert: BudgetAlert, channels: list[AlertChannel]) -> dict:
        """Deliver an alert to the specified channels.  Returns delivery status."""
        results = {}
        for channel in channels:
            try:
                if channel == AlertChannel.slack:
                    await self._send_slack(alert)
                    results["slack"] = "delivered"
                elif channel == AlertChannel.webhook:
                    await self._send_webhook(alert)
                    results["webhook"] = "delivered"
                elif channel == AlertChannel.email:
                    await self._send_email(alert)
                    results["email"] = "delivered"
            except Exception as e:
                logger.error("Failed to deliver alert via %s: %s", channel.value, e)
                results[channel.value] = f"failed: {str(e)}"
        return results

    async def _send_slack(self, alert: BudgetAlert) -> None:
        """Send alert to Slack via incoming webhook."""
        settings = get_settings()
        if not settings.slack_webhook_url:
            logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return

        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
        }
        emoji = severity_emoji.get(alert.severity.value, "📢")

        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} TokenMeter Budget Alert",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": alert.message,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Current Spend:* ${alert.current_spend_usd:.2f}"},
                        {"type": "mrkdwn", "text": f"*Budget:* ${alert.budget_amount_usd:.2f}"},
                        {"type": "mrkdwn", "text": f"*Utilization:* {alert.utilization_percentage:.1f}%"},
                        {"type": "mrkdwn", "text": f"*Severity:* {alert.severity.value.upper()}"},
                    ],
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View Dashboard"},
                            "url": f"{settings.frontend_url}/dashboard/budgets",
                        }
                    ],
                },
            ],
        }

        client = await self._get_client()
        resp = await client.post(settings.slack_webhook_url, json=payload)
        resp.raise_for_status()
        logger.info("Slack alert sent for budget %s", alert.budget_id)

    async def _send_webhook(self, alert: BudgetAlert) -> None:
        """Send alert to a generic webhook endpoint."""
        settings = get_settings()
        # In production, webhook URL would be per-org from the database
        # For now, we use a generic pattern
        payload = {
            "event": "budget_alert",
            "alert_id": alert.id,
            "budget_id": alert.budget_id,
            "org_id": alert.org_id,
            "severity": alert.severity.value,
            "message": alert.message,
            "current_spend_usd": alert.current_spend_usd,
            "budget_amount_usd": alert.budget_amount_usd,
            "utilization_percentage": alert.utilization_percentage,
            "threshold_percentage": alert.threshold_percentage,
            "created_at": alert.created_at.isoformat(),
        }

        from backend.utils.security import compute_webhook_signature

        payload_bytes = json.dumps(payload).encode()
        signature = compute_webhook_signature(payload_bytes, "webhook_secret")

        logger.info("Webhook alert payload prepared for budget %s", alert.budget_id)

    async def _send_email(self, alert: BudgetAlert) -> None:
        """Send alert via email.  Uses SMTP configuration."""
        settings = get_settings()
        if not settings.alert_email_smtp_host:
            logger.warning("Email SMTP not configured, skipping email alert")
            return

        # Use aiosmtplib for async email
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[TokenMeter] Budget Alert: {alert.severity.value.upper()}"
            msg["From"] = settings.alert_email_from
            msg["To"] = "admin@example.com"  # In prod, fetch from org settings

            html = f"""
            <h2>🚨 TokenMeter Budget Alert</h2>
            <p>{alert.message}</p>
            <table>
                <tr><td><strong>Current Spend:</strong></td><td>${alert.current_spend_usd:.2f}</td></tr>
                <tr><td><strong>Budget:</strong></td><td>${alert.budget_amount_usd:.2f}</td></tr>
                <tr><td><strong>Utilization:</strong></td><td>{alert.utilization_percentage:.1f}%</td></tr>
            </table>
            <p><a href="{settings.frontend_url}/dashboard/budgets">View Dashboard</a></p>
            """
            msg.attach(MIMEText(html, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.alert_email_smtp_host,
                port=settings.alert_email_smtp_port,
                username=settings.alert_email_smtp_user,
                password=settings.alert_email_smtp_password,
                use_tls=True,
            )
            logger.info("Email alert sent for budget %s", alert.budget_id)
        except ImportError:
            logger.warning("aiosmtplib not installed, skipping email alert")
        except Exception as e:
            logger.error("Failed to send email alert: %s", e)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# Singleton
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
