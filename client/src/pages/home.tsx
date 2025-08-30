import Header from "@/components/header";
import HeroSection from "@/components/hero-section";
import StreaksTable from "@/components/streaks-table";
import AnalyticsSection from "@/components/analytics-section";
import AboutSection from "@/components/about-section";
import Footer from "@/components/footer";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <HeroSection />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StreaksTable />
        <AnalyticsSection />
        <AboutSection />
      </main>
      <Footer />
    </div>
  );
}
