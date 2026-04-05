import { useEffect, useMemo, useState } from "react";

import { toast } from "../../components/ui";
import { presaleApi } from "../../services/api";
import { normalizeTemplate } from "./utils";

export function usePresaleTemplates() {
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyingTemplateId, setApplyingTemplateId] = useState(null);
  const [ratingTemplateId, setRatingTemplateId] = useState(null);
  const [myRatings, setMyRatings] = useState({});

  useEffect(() => {
    const loadTemplates = async () => {
      try {
        setLoading(true);
        const response = await presaleApi.templates.list({ page: 1, page_size: 100 });
        const payload = response?.data;
        const items =
          payload?.items ||
          payload?.data?.items ||
          payload?.data ||
          response?.items ||
          response?.data ||
          [];

        if (Array.isArray(items) && items.length > 0) {
          setTemplates(items.map((item, index) => normalizeTemplate(item, index)));
        } else {
          setTemplates([]);
        }
        setLoadError(null);
      } catch (_error) {
        setTemplates([]);
        setLoadError(_error.response?.data?.detail || _error.message || "加载模板数据失败");
      } finally {
        setLoading(false);
      }
    };

    loadTemplates();
  }, []);

  const categories = useMemo(() => {
    const counter = (templates || []).reduce((acc, template) => {
      const key = template.category || "通用";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const dynamicCategories = Object.entries(counter).map(([category, count]) => ({
      key: category,
      label: category,
      count,
    }));

    return [
      { key: "all", label: "全部模板", count: templates.length },
      ...dynamicCategories,
    ];
  }, [templates]);

  const filteredTemplates = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase();

    return (templates || []).filter((template) => {
      const matchCategory =
        selectedCategory === "all" || template.category === selectedCategory;

      if (!matchCategory) {
        return false;
      }

      if (!lowerKeyword) {
        return true;
      }

      const searchableText = [
        template.name,
        template.description,
        ...(template.tags || []),
        ...(template.scenarios || []),
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(lowerKeyword);
    });
  }, [keyword, selectedCategory, templates]);

  const stats = useMemo(() => {
    const totalApplyCount = (templates || []).reduce(
      (sum, template) => sum + (template.applyCount || 0),
      0,
    );
    const averageRating =
      templates.length > 0
        ? templates.reduce((sum, template) => sum + (template.rating || 0), 0) /
          templates.length
        : 0;

    return {
      total: templates.length,
      categories: Math.max(0, categories.length - 1),
      totalApplyCount,
      averageRating,
    };
  }, [categories.length, templates]);

  const applyTemplate = async (template) => {
    if (!template) {
      return;
    }

    setApplyingTemplateId(template.id);

    const nextApplyCount = (template.applyCount || 0) + 1;
    setTemplates((prev) =>
      (prev || []).map((item) =>
        item.id === template.id ? { ...item, applyCount: nextApplyCount } : item,
      ),
    );

    try {
      await presaleApi.templates.update(template.id, {
        apply_count: nextApplyCount,
      });
      toast.success(`模板「${template.name}」已应用`);
    } catch (_error) {
      toast.warning(`模板「${template.name}」已本地应用，后台同步稍后重试`);
    } finally {
      setApplyingTemplateId(null);
    }
  };

  const rateTemplate = async (template, score) => {
    if (!template || !score) {
      return;
    }

    setRatingTemplateId(template.id);
    setMyRatings((prev) => ({ ...prev, [template.id]: score }));

    const nextRatingCount = (template.ratingCount || 0) + 1;
    const nextRating =
      ((template.rating || 0) * (template.ratingCount || 0) + score) /
      nextRatingCount;

    setTemplates((prev) =>
      (prev || []).map((item) =>
        item.id === template.id
          ? { ...item, rating: nextRating, ratingCount: nextRatingCount }
          : item,
      ),
    );

    try {
      await presaleApi.templates.update(template.id, { rating: score });
      toast.success(`已提交 ${score} 星评分`);
    } catch (_error) {
      toast.warning("评分已本地保存，后台同步稍后重试");
    } finally {
      setRatingTemplateId(null);
    }
  };

  const openPreview = async (template) => {
    if (!template) {
      return;
    }

    setPreviewTemplate(template);
    setPreviewLoading(true);

    try {
      const response = await presaleApi.templates.get(template.id);
      const detailData = response?.data?.data || response?.data || {};
      const mergedTemplate = normalizeTemplate(
        { ...template, ...detailData },
        0,
      );
      setPreviewTemplate(mergedTemplate);
    } catch (_error) {
      setPreviewTemplate(template);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreview = () => setPreviewTemplate(null);

  return {
    loading,
    loadError,
    templates,
    keyword,
    setKeyword,
    selectedCategory,
    setSelectedCategory,
    previewTemplate,
    previewLoading,
    applyingTemplateId,
    ratingTemplateId,
    myRatings,
    categories,
    filteredTemplates,
    stats,
    applyTemplate,
    rateTemplate,
    openPreview,
    closePreview,
  };
}
