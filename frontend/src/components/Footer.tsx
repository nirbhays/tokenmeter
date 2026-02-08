import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50">
      <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Product</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/#features" className="text-sm text-gray-600 hover:text-gray-900">Features</Link></li>
              <li><Link href="/#pricing" className="text-sm text-gray-600 hover:text-gray-900">Pricing</Link></li>
              <li><Link href="/docs" className="text-sm text-gray-600 hover:text-gray-900">Documentation</Link></li>
              <li><Link href="/changelog" className="text-sm text-gray-600 hover:text-gray-900">Changelog</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Developers</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/docs/api" className="text-sm text-gray-600 hover:text-gray-900">API Reference</Link></li>
              <li><Link href="/docs/sdks" className="text-sm text-gray-600 hover:text-gray-900">SDKs</Link></li>
              <li><Link href="https://github.com/tokenmeter" className="text-sm text-gray-600 hover:text-gray-900">GitHub</Link></li>
              <li><Link href="/docs/self-host" className="text-sm text-gray-600 hover:text-gray-900">Self-Host</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Company</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/about" className="text-sm text-gray-600 hover:text-gray-900">About</Link></li>
              <li><Link href="/blog" className="text-sm text-gray-600 hover:text-gray-900">Blog</Link></li>
              <li><Link href="/careers" className="text-sm text-gray-600 hover:text-gray-900">Careers</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Legal</h3>
            <ul className="mt-3 space-y-2">
              <li><Link href="/privacy" className="text-sm text-gray-600 hover:text-gray-900">Privacy</Link></li>
              <li><Link href="/terms" className="text-sm text-gray-600 hover:text-gray-900">Terms</Link></li>
              <li><Link href="/security" className="text-sm text-gray-600 hover:text-gray-900">Security</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-200 pt-8 flex items-center justify-between">
          <p className="text-sm text-gray-500">© 2026 TokenMeter. All rights reserved.</p>
          <div className="flex items-center gap-2">
            <span className="text-2xl">⚡</span>
            <span className="font-bold text-gray-900">TokenMeter</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
