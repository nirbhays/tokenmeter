"use client";

export default function SettingsPage() {
  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-500 mb-8">Manage your organization, billing, and integrations</p>

          {/* Organization */}
          <section className="bg-white rounded-2xl border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Organization</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input type="text" defaultValue="My Organization" className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Slug</label>
                <input type="text" defaultValue="my-org" className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm" />
              </div>
            </div>
          </section>

          {/* Billing */}
          <section className="bg-white rounded-2xl border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Billing</h2>
            <div className="flex items-center justify-between p-4 bg-brand-50 rounded-xl border border-brand-200">
              <div>
                <p className="font-semibold text-gray-900">Pro Plan</p>
                <p className="text-sm text-gray-600">$49/month • 500K requests/month</p>
              </div>
              <button className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium hover:bg-gray-50">
                Manage Subscription
              </button>
            </div>
          </section>

          {/* Provider Credentials */}
          <section className="bg-white rounded-2xl border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Provider API Keys</h2>
            <p className="text-sm text-gray-500 mb-4">
              Add your LLM provider API keys. These are encrypted and stored securely.
            </p>
            <div className="space-y-3">
              {[
                { name: "OpenAI", env: "OPENAI_API_KEY", connected: true },
                { name: "Anthropic", env: "ANTHROPIC_API_KEY", connected: true },
                { name: "Google", env: "GOOGLE_API_KEY", connected: false },
              ].map((provider) => (
                <div key={provider.name} className="flex items-center justify-between p-4 rounded-xl border">
                  <div className="flex items-center gap-3">
                    <span className={`h-2.5 w-2.5 rounded-full ${provider.connected ? "bg-green-500" : "bg-gray-300"}`} />
                    <div>
                      <p className="font-medium">{provider.name}</p>
                      <p className="text-xs text-gray-500">{provider.env}</p>
                    </div>
                  </div>
                  <button className="text-sm text-brand-600 hover:text-brand-700">
                    {provider.connected ? "Update" : "Connect"}
                  </button>
                </div>
              ))}
            </div>
          </section>

          {/* Integrations */}
          <section className="bg-white rounded-2xl border p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Integrations</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 rounded-xl border">
                <div>
                  <p className="font-medium">Slack</p>
                  <p className="text-sm text-gray-500">Receive budget alerts in Slack</p>
                </div>
                <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500">
                  Connect
                </button>
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl border">
                <div>
                  <p className="font-medium">Webhooks</p>
                  <p className="text-sm text-gray-500">Send alerts to custom webhook endpoints</p>
                </div>
                <button className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50">
                  Configure
                </button>
              </div>
            </div>
          </section>

          {/* Danger Zone */}
          <section className="bg-white rounded-2xl border border-red-200 p-6">
            <h2 className="text-lg font-semibold text-red-600 mb-4">Danger Zone</h2>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Delete Organization</p>
                <p className="text-sm text-gray-500">Permanently delete this organization and all its data</p>
              </div>
              <button className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50">
                Delete
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
