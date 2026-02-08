import Link from "next/link";

const features = [
  {
    title: "Real-Time Cost Tracking",
    description:
      "See exactly what every API call costs — broken down by model, team, and feature. No more surprise bills.",
    icon: "📊",
  },
  {
    title: "Smart Routing",
    description:
      'Automatically route simple queries to cheap models (GPT-4.1-nano at $0.10/1M tokens) and complex ones to powerful models. Save up to 60%.',
    icon: "🧠",
  },
  {
    title: "Budget Alerts",
    description:
      "Set spend thresholds per team, feature, or model. Get Slack/webhook alerts before you blow your budget.",
    icon: "🚨",
  },
  {
    title: "Drop-In SDKs",
    description:
      "Change one line of code. Replace `from openai import OpenAI` with `from tokenmeter import OpenAI`. Done.",
    icon: "⚡",
  },
  {
    title: "OpenAI-Compatible Proxy",
    description:
      "Works with any app that uses the OpenAI API format. Just change the base URL. Supports streaming SSE.",
    icon: "🔄",
  },
  {
    title: "Multi-Provider Support",
    description:
      "OpenAI, Anthropic, Google — all through one API. Route across providers for the best price-performance.",
    icon: "🌐",
  },
];

const pricingTiers = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started — track your first 10K requests",
    features: [
      "10,000 requests/month",
      "Basic dashboard",
      "Cost tracking",
      "2 API keys",
      "7-day data retention",
    ],
    cta: "Start Free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/month",
    description: "For teams serious about AI cost optimization",
    features: [
      "500,000 requests/month",
      "Advanced dashboard",
      "Smart routing",
      "Budget alerts (Slack + webhook)",
      "20 API keys",
      "90-day data retention",
      "Team management",
      "Response caching",
    ],
    cta: "Start Pro Trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "$299",
    period: "/month",
    description: "For organizations running AI at scale",
    features: [
      "10M+ requests/month",
      "Custom routing rules",
      "Semantic caching",
      "Unlimited API keys",
      "Unlimited retention",
      "SSO / SAML",
      "Zero-logging mode",
      "Dedicated support + SLA",
      "Data residency options",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-gray-50 via-white to-brand-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center rounded-full bg-brand-100 px-4 py-1.5 text-sm font-medium text-brand-700">
              🚀 Now tracking $2M+ in AI spend
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-7xl">
              Know exactly what you{" "}
              <span className="gradient-text">spend on AI</span>
            </h1>
            <p className="mt-6 text-xl leading-8 text-gray-600">
              TokenMeter is a drop-in proxy that tracks every LLM API call,
              calculates real-time costs, and intelligently routes requests to
              save you up to 60% on AI spend.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/dashboard"
                className="rounded-xl bg-brand-600 px-8 py-4 text-lg font-semibold text-white shadow-lg hover:bg-brand-500 transition-all duration-200 hover:-translate-y-0.5"
              >
                Start Tracking — Free
              </Link>
              <Link
                href="https://github.com/tokenmeter/tokenmeter"
                className="text-lg font-semibold leading-6 text-gray-700 hover:text-brand-600 transition-colors"
              >
                View on GitHub →
              </Link>
            </div>
          </div>

          {/* Code snippet */}
          <div className="mx-auto mt-16 max-w-2xl">
            <div className="rounded-2xl bg-gray-900 p-6 shadow-2xl ring-1 ring-white/10">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <div className="h-3 w-3 rounded-full bg-yellow-500" />
                <div className="h-3 w-3 rounded-full bg-green-500" />
                <span className="ml-2 text-xs text-gray-400 font-mono">
                  one-line-change.py
                </span>
              </div>
              <pre className="text-sm font-mono overflow-x-auto">
                <code>
                  <span className="text-gray-500"># Before</span>
                  {"\n"}
                  <span className="text-red-400 line-through opacity-60">
                    from openai import OpenAI
                  </span>
                  {"\n\n"}
                  <span className="text-gray-500"># After — that&apos;s it!</span>
                  {"\n"}
                  <span className="text-green-400">
                    from tokenmeter import OpenAI
                  </span>
                  {"\n\n"}
                  <span className="text-blue-300">client</span>
                  <span className="text-gray-300"> = </span>
                  <span className="text-yellow-300">OpenAI</span>
                  <span className="text-gray-300">()</span>
                  {"\n"}
                  <span className="text-blue-300">response</span>
                  <span className="text-gray-300">
                    {" = client.chat.completions.create("}
                  </span>
                  {"\n"}
                  <span className="text-gray-300">{"    model="}</span>
                  <span className="text-green-300">&quot;gpt-4.1&quot;</span>
                  <span className="text-gray-300">,</span>
                  {"\n"}
                  <span className="text-gray-300">{"    messages=[{"}
                  </span>
                  <span className="text-green-300">&quot;role&quot;</span>
                  <span className="text-gray-300">: </span>
                  <span className="text-green-300">&quot;user&quot;</span>
                  <span className="text-gray-300">, </span>
                  <span className="text-green-300">&quot;content&quot;</span>
                  <span className="text-gray-300">: </span>
                  <span className="text-green-300">&quot;Hello!&quot;</span>
                  <span className="text-gray-300">{"}]"}</span>
                  {"\n"}
                  <span className="text-gray-300">{")"}</span>
                </code>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 sm:py-32" id="features">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Everything you need to control AI costs
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              From tracking individual API calls to optimizing company-wide AI
              spend.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-gray-200 bg-white p-8 card-hover"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section
        className="py-24 sm:py-32 bg-gray-50"
        id="pricing"
      >
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              Start free. Upgrade when you need smart routing and team features.
            </p>
          </div>
          <div className="mx-auto mt-16 grid max-w-5xl grid-cols-1 gap-8 lg:grid-cols-3">
            {pricingTiers.map((tier) => (
              <div
                key={tier.name}
                className={`rounded-2xl p-8 ${
                  tier.highlighted
                    ? "bg-brand-600 text-white ring-2 ring-brand-600 shadow-2xl scale-105"
                    : "bg-white border border-gray-200"
                }`}
              >
                <h3
                  className={`text-lg font-semibold ${
                    tier.highlighted ? "text-brand-100" : "text-gray-500"
                  }`}
                >
                  {tier.name}
                </h3>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  <span
                    className={`text-sm ${
                      tier.highlighted ? "text-brand-200" : "text-gray-500"
                    }`}
                  >
                    {tier.period}
                  </span>
                </div>
                <p
                  className={`mt-2 text-sm ${
                    tier.highlighted ? "text-brand-100" : "text-gray-600"
                  }`}
                >
                  {tier.description}
                </p>
                <ul className="mt-6 space-y-3">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <span className={tier.highlighted ? "text-brand-200" : "text-brand-600"}>
                        ✓
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/dashboard"
                  className={`mt-8 block w-full rounded-lg py-3 text-center font-semibold transition-all ${
                    tier.highlighted
                      ? "bg-white text-brand-600 hover:bg-brand-50"
                      : "bg-brand-600 text-white hover:bg-brand-500"
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Stop guessing. Start tracking.
          </h2>
          <p className="mt-4 text-xl text-gray-600">
            Join hundreds of teams who&apos;ve saved thousands on AI costs with
            TokenMeter.
          </p>
          <Link
            href="/dashboard"
            className="mt-8 inline-block rounded-xl bg-brand-600 px-8 py-4 text-lg font-semibold text-white shadow-lg hover:bg-brand-500 transition-all duration-200 hover:-translate-y-0.5"
          >
            Get Started — Free Forever
          </Link>
        </div>
      </section>
    </div>
  );
}
