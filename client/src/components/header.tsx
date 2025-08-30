import { Link } from "wouter";

export default function Header() {
  return (
    <header className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            <Link href="/" className="flex items-center space-x-2" data-testid="header-logo">
              <span className="text-primary text-2xl">♔</span>
              <h1 className="text-xl font-bold text-foreground">Interesting Chess</h1>
            </Link>
            <span className="hidden sm:inline-block text-sm text-muted-foreground">
              Anomalous Win Streaks Tracker
            </span>
          </div>
          <nav className="flex items-center space-x-6">
            <a 
              href="#streaks" 
              className="text-foreground hover:text-primary transition-colors"
              data-testid="nav-streaks"
            >
              Streaks
            </a>
            <a 
              href="#analytics" 
              className="text-foreground hover:text-primary transition-colors"
              data-testid="nav-analytics"
            >
              Analytics
            </a>
            <a 
              href="#about" 
              className="text-foreground hover:text-primary transition-colors"
              data-testid="nav-about"
            >
              About
            </a>
          </nav>
        </div>
      </div>
    </header>
  );
}
