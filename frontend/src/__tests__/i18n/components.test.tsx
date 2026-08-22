import React from "react";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { ThemeProvider } from "next-themes";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { LanguageSwitcher } from "@/components/language/LanguageSwitcher";

// Mock hooks
jest.mock("next-intl", () => ({
  useTranslations: () => (key: string) => `[translated] ${key}`,
}));

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock("next-themes", () => ({
  useTheme: () => ({ theme: "light", setTheme: jest.fn() }),
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock("@/hooks/use-auth", () => ({
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
    isAdmin: false,
    logout: jest.fn(),
  }),
}));

jest.mock("@/hooks/useLanguage", () => ({
  useLanguage: () => ({
    currentLanguage: "en",
    availableLanguages: [{ code: "en", nativeName: "English", name: "English" }],
    changeLanguage: jest.fn(),
    isPending: false,
  }),
}));

const renderWithMockIntl = (component: React.ReactNode) => {
  return render(
    <ThemeProvider>{component}</ThemeProvider>
  );
};

describe("I18n Components Translation", () => {
  it("renders Navbar with translated strings", () => {
    renderWithMockIntl(<Navbar />);
    expect(screen.getByText("[translated] brand")).toBeInTheDocument();
    expect(screen.getAllByText("[translated] schemes")[0]).toBeInTheDocument();
    expect(screen.getAllByText("[translated] eligibility")[0]).toBeInTheDocument();
    expect(screen.getAllByText("[translated] chat")[0]).toBeInTheDocument();
    expect(screen.getAllByText("[translated] login")[0]).toBeInTheDocument();
  });

  it("renders Footer with translated strings", () => {
    renderWithMockIntl(<Footer />);
    expect(screen.getByText("[translated] dashboard")).toBeInTheDocument();
    expect(screen.getByText("[translated] privacy")).toBeInTheDocument();
    expect(screen.getByText("[translated] terms")).toBeInTheDocument();
  });

  it("renders LanguageSwitcher", () => {
    renderWithMockIntl(<LanguageSwitcher />);
    expect(screen.getByLabelText("[translated] language_switcher")).toBeInTheDocument();
  });
});
