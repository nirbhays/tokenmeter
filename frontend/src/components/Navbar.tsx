import Link from "next/link";

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-lg">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              <span className="text-xl font-bold text-gray-900">TokenMeter</span>
            </Link>
            <div className="hidden md:flex items-center gap-6">
              <Link href="/#features" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Features
              </Link>
              <Link href="/#pricing" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Pricing
              </Link>
              <Link href="/docs" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                Docs
              </Link>
              <Link href="https://github.com/tokenmeter/tokenmeter" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
                GitHub
              </Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900 transition-colors">
              Sign In
            </Link>
            <Link
              href="/dashboard"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
