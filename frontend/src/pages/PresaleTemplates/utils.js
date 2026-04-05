export function normalizeStringArray(value) {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(/[,\n，]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

export function normalizeOutline(value) {
  if (!value) {
    return [];
  }

  let parsedValue = value;
  if (typeof parsedValue === "string") {
    try {
      parsedValue = JSON.parse(parsedValue);
    } catch (_error) {
      parsedValue = [];
    }
  }

  if (!Array.isArray(parsedValue)) {
    return [];
  }

  return parsedValue.map((section, index) => {
    if (typeof section === "string") {
      return { title: section, bullets: [] };
    }
    const title =
      section?.title ||
      section?.name ||
      section?.section_name ||
      `章节 ${index + 1}`;
    const bullets = normalizeStringArray(
      section?.bullets || section?.items || section?.points || section?.content,
    );
    return { title, bullets };
  });
}

export function normalizeTemplate(item, index = 0) {
  const ratingRaw =
    item?.avg_rating ?? item?.rating_score ?? item?.rating ?? item?.score ?? 4.5;
  const rating = Number.isFinite(Number(ratingRaw))
    ? Math.min(5, Math.max(0, Number(ratingRaw)))
    : 4.5;

  const ratingCountRaw = item?.rating_count ?? item?.ratingCount ?? 0;
  const ratingCount = Number.isFinite(Number(ratingCountRaw))
    ? Math.max(0, Number(ratingCountRaw))
    : 0;

  const applyCountRaw =
    item?.apply_count ?? item?.usage_count ?? item?.used_count ?? 0;
  const applyCount = Number.isFinite(Number(applyCountRaw))
    ? Math.max(0, Number(applyCountRaw))
    : 0;

  const outline = normalizeOutline(
    item?.outline ||
      item?.template_outline ||
      item?.preview_outline ||
      item?.sections,
  );

  return {
    id: item?.id || item?.template_id || `template-${index + 1}`,
    name: item?.template_name || item?.name || `售前模板 ${index + 1}`,
    category: item?.category || item?.template_category || item?.type || "通用",
    description:
      item?.description ||
      item?.summary ||
      "该模板覆盖标准售前活动，可用于快速复用与协同交付。",
    tags: normalizeStringArray(item?.tags || item?.keywords),
    scenarios: normalizeStringArray(
      item?.scenarios || item?.applicable_scenarios || item?.applicable_scene,
    ),
    outline,
    deliverables: normalizeStringArray(
      item?.deliverables || item?.outputs || item?.output_items,
    ),
    rating,
    ratingCount,
    applyCount,
    owner:
      item?.owner_name ||
      item?.owner ||
      item?.created_by_name ||
      item?.created_by ||
      "售前团队",
    updatedAt:
      item?.updated_at ||
      item?.updatedAt ||
      item?.last_modified_at ||
      item?.created_at ||
      new Date().toISOString(),
  };
}
