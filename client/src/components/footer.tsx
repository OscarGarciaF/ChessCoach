export default function Footer() {
  return (
    <footer className="bg-muted border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-primary text-xl">♔</span>
              <span className="font-semibold text-foreground">Interesting Chess</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Statistical analysis of chess win streaks using public Chess.com data.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-foreground mb-3">Resources</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <a href="https://www.chess.com/news/view/published-data-api" 
                   className="hover:text-primary transition-colors"
                   target="_blank"
                   rel="noopener noreferrer"
                   data-testid="footer-link-api">
                  Chess.com API
                </a>
              </li>
              <li>
                <a href="https://en.wikipedia.org/wiki/Glicko_rating_system" 
                   className="hover:text-primary transition-colors"
                   target="_blank"
                   rel="noopener noreferrer"
                   data-testid="footer-link-glicko">
                  Glicko Rating System
                </a>
              </li>
              <li>
                <a href="#about" 
                   className="hover:text-primary transition-colors"
                   data-testid="footer-link-methods">
                  Statistical Methods
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-foreground mb-3">Contact</h3>
            <p className="text-sm text-muted-foreground">
              For questions or suggestions about this analysis tool.
            </p>
            <div className="mt-3">
              <a 
                href="mailto:contact@interestingchess.com" 
                className="text-sm text-primary hover:underline"
                data-testid="footer-contact-email"
              >
                contact@interestingchess.com
              </a>
            </div>
          </div>
        </div>
        <div className="border-t border-border mt-8 pt-6 text-center">
          <p className="text-sm text-muted-foreground">
            © 2024 Interesting Chess. Data sourced from Chess.com Public API. 
            <span className="mx-2">•</span>
            Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>
      </div>
    </footer>
  );
}
