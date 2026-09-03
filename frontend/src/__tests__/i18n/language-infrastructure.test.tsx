import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { useLanguageStore, AVAILABLE_LANGUAGES } from "@/store/language-store";
import { LanguageSwitcher } from "@/components/language/LanguageSwitcher";
import { useLanguage } from "@/hooks/useLanguage";

// Mock the next-intl hooks and our routing
jest.mock("next-intl", () => ({
  useLocale: () => "en",
  useTranslations: () => (key: string) => key,
}));

const mockRouterReplace = jest.fn();
jest.mock("@/i18n/routing", () => ({
  useRouter: () => ({
    replace: mockRouterReplace,
  }),
  usePathname: () => "/schemes",
  locales: ["en", "hi", "ta"],
  defaultLocale: "en",
}));

// A test component to test the hook independently
function HookTestComponent() {
  const { currentLanguage, availableLanguages, changeLanguage } = useLanguage();
  return (
    <div>
      <span data-testid="current-lang">{currentLanguage}</span>
      <span data-testid="available-count">{availableLanguages.length}</span>
      <button onClick={() => changeLanguage("hi")}>Change to Hindi</button>
    </div>
  );
}

describe("Multilingual Infrastructure", () => {
  beforeEach(() => {
    useLanguageStore.setState({ currentLanguage: "en" });
  });

  describe("Language Store", () => {
    it("should initialize with English", () => {
      const state = useLanguageStore.getState();
      expect(state.currentLanguage).toBe("en");
    });

    it("should update language", () => {
      useLanguageStore.getState().setLanguage("hi");
      expect(useLanguageStore.getState().currentLanguage).toBe("hi");
    });
  });

  describe("useLanguage Hook", () => {
    it("should provide current language and available languages", () => {
      render(<HookTestComponent />);
      expect(screen.getByTestId("current-lang")).toHaveTextContent("en");
      expect(screen.getByTestId("available-count")).toHaveTextContent(
        String(AVAILABLE_LANGUAGES.length),
      );
    });

    it("should call router.replace when language is changed", () => {
      render(<HookTestComponent />);
      fireEvent.click(screen.getByText("Change to Hindi"));
      expect(mockRouterReplace).toHaveBeenCalledWith("/schemes", { locale: "hi" });
    });
  });

  describe("Language Switcher Component", () => {
    it("should render with the current language native name", () => {
      render(<LanguageSwitcher />);
      expect(screen.getByText("English")).toBeInTheDocument();
    });

    it("should open dropdown and show available languages", () => {
      render(<LanguageSwitcher />);
      
      const button = screen.getByRole("button", { expanded: false });
      fireEvent.click(button);

      expect(screen.getByRole("menu")).toBeInTheDocument();
      expect(screen.getByText("हिन्दी")).toBeInTheDocument();
      expect(screen.getByText("தமிழ்")).toBeInTheDocument();
    });
  });
});
