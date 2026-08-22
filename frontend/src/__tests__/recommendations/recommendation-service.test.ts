/**
 * Recommendation Service Tests — Sahayak AI (Phase 5)
 * Tests HTTP client functions via mocked axios.
 * Validates correct endpoints, params, and return shapes.
 */

// Declare typed refs for mock functions — assigned after jest.mock hoisting
let mockGet: jest.Mock;
let mockPost: jest.Mock;

// jest.mock is hoisted by the transform — factory runs before any imports
jest.mock("@/lib/axios", () => {
  const getMock = jest.fn();
  const postMock = jest.fn();
  return {
    __esModule: true,
    default: { get: getMock, post: postMock },
    // Export for test access
    __getMock: getMock,
    __postMock: postMock,
  };
});

// Import AFTER mock registration
import apiClient from "@/lib/axios";
import { recommendationService } from "@/services/recommendation.service";
import type {
  RecommendationResponse,
  TopRecommendationsResponse,
  RecommendationDetail,
  RecommendationRefreshResponse,
  ProfileCompletionResponse,
} from "@/types/recommendation";

// Shared test data
const SCHEME_ID = "abc-123-scheme";

const MOCK_SUMMARY = {
  scheme_id: SCHEME_ID,
  scheme_name: "PM-KISAN",
  scheme_code: "PM-KISAN-2024",
  scheme_type: "central",
  category: "agriculture",
  ministry: "Ministry of Agriculture",
  state: null,
  is_featured: true,
  official_url: "https://pmkisan.gov.in",
  short_description: "Income support for farmers.",
  recommendation_score: 92.5,
  priority: "HIGH" as const,
  eligibility_status: "eligible" as const,
  eligible: true,
  reasons: [{ reason_type: "eligibility" as const, text: "You qualify." }],
  missing_information: [],
};

beforeAll(() => {
  // Bind typed refs to the mock fns after module init
  mockGet = apiClient.get as jest.Mock;
  mockPost = apiClient.post as jest.Mock;
});

beforeEach(() => {
  mockGet?.mockReset?.();
  mockPost?.mockReset?.();
});

// ── getRecommendations ─────────────────────────────────────────────────────

describe("recommendationService.getRecommendations", () => {
  test("calls GET /api/v1/recommendations with no params", async () => {
    const mockData: RecommendationResponse = {
      success: true,
      message: "OK",
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
      data: [MOCK_SUMMARY],
    };
    mockGet.mockResolvedValueOnce({ data: mockData });

    const result = await recommendationService.getRecommendations();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/recommendations", {
      params: {},
    });
    expect(result.total).toBe(1);
    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    expect(result.data[0]!.scheme_name).toBe("PM-KISAN");
  });

  test("passes priority filter as query param", async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        message: "OK",
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 1,
        data: [],
      },
    });

    await recommendationService.getRecommendations({ priority: "HIGH" });

    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/recommendations",
      expect.objectContaining({
        params: expect.objectContaining({ priority: "HIGH" }),
      })
    );
  });

  test("passes sort param", async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        success: true,
        message: "OK",
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 1,
        data: [],
      },
    });

    await recommendationService.getRecommendations({ sort: "alphabetical" });

    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/recommendations",
      expect.objectContaining({
        params: expect.objectContaining({ sort: "alphabetical" }),
      })
    );
  });
});

// ── getTopRecommendations ──────────────────────────────────────────────────

describe("recommendationService.getTopRecommendations", () => {
  test("calls GET /api/v1/recommendations/top with default limit=5", async () => {
    const mockData: TopRecommendationsResponse = {
      success: true,
      message: "OK",
      data: [MOCK_SUMMARY],
    };
    mockGet.mockResolvedValueOnce({ data: mockData });

    const result = await recommendationService.getTopRecommendations();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/recommendations/top", {
      params: { limit: 5 },
    });
    expect(result.data).toHaveLength(1);
  });

  test("passes custom limit", async () => {
    mockGet.mockResolvedValueOnce({
      data: { success: true, message: "OK", data: [] },
    });

    await recommendationService.getTopRecommendations(3);

    expect(mockGet).toHaveBeenCalledWith(
      "/api/v1/recommendations/top",
      expect.objectContaining({ params: { limit: 3 } })
    );
  });
});

// ── getRecommendation ──────────────────────────────────────────────────────

describe("recommendationService.getRecommendation", () => {
  test("calls GET /api/v1/recommendations/:id", async () => {
    const mockDetail: Partial<RecommendationDetail> = {
      scheme_id: SCHEME_ID,
      scheme_name: "PM-KISAN",
      recommendation_score: 92.5,
      priority: "HIGH",
      eligible: true,
      eligibility_status: "eligible",
      reasons: [],
      missing_information: [],
      passed_rules: [],
      failed_rules: [],
      evaluated_at: new Date().toISOString(),
    };
    mockGet.mockResolvedValueOnce({ data: mockDetail });

    const result = await recommendationService.getRecommendation(SCHEME_ID);

    expect(mockGet).toHaveBeenCalledWith(
      `/api/v1/recommendations/${SCHEME_ID}`
    );
    expect(result.scheme_id).toBe(SCHEME_ID);
  });
});

// ── refreshRecommendations ─────────────────────────────────────────────────

describe("recommendationService.refreshRecommendations", () => {
  test("calls POST /api/v1/recommendations/refresh", async () => {
    const mockRefresh: RecommendationRefreshResponse = {
      success: true,
      message: "Recommendations refreshed successfully.",
      total_recommendations: 7,
      refreshed_at: new Date().toISOString(),
    };
    mockPost.mockResolvedValueOnce({ data: mockRefresh });

    const result = await recommendationService.refreshRecommendations();

    expect(mockPost).toHaveBeenCalledWith("/api/v1/recommendations/refresh");
    expect(result.success).toBe(true);
    expect(result.total_recommendations).toBe(7);
  });
});

// ── getProfileCompletion ───────────────────────────────────────────────────

describe("recommendationService.getProfileCompletion", () => {
  test("calls GET /api/v1/recommendations/profile", async () => {
    const mockProfile: ProfileCompletionResponse = {
      success: true,
      completion_percentage: 70.0,
      filled_count: 7,
      total_fields: 10,
      missing_fields: ["District", "Education Level", "Disability Status"],
      fields: [],
    };
    mockGet.mockResolvedValueOnce({ data: mockProfile });

    const result = await recommendationService.getProfileCompletion();

    expect(mockGet).toHaveBeenCalledWith("/api/v1/recommendations/profile");
    expect(result.completion_percentage).toBe(70.0);
    expect(result.missing_fields).toContain("District");
  });
});
