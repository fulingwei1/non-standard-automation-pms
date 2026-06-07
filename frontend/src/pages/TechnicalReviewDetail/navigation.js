export function buildTechnicalReviewListPath(search) {
    const params = new URLSearchParams(search?.toString() || "");
    const query = params.toString();
    return `/technical-reviews${query ? `?${query}` : ""}`;
}
