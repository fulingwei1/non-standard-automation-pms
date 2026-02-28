/**
 * Category Tree Component - Knowledge base category navigation
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Search,
  BookOpen,
  ChevronUp } from
"lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { TrendingUp } from "lucide-react";
import {
  generateCategoryTree,
  getPopularCategories,
  getCategoryConfig,
  formatCategory
} from
"@/lib/constants/knowledge";

export default function CategoryTree({
  categories = null,
  onCategorySelect,
  selectedCategory = null,
  selectedSubcategory: _selectedSubcategory = null,
  expandedCategories = [],
  onExpandToggle,
  showStats = true,
  showSearch = true,
  compact = false,
  variant = "default"
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [localExpanded, setLocalExpanded] = useState(expandedCategories);

  // Use provided categories or generate from config
  const categoryTree = categories || generateCategoryTree();

  // Get popular categories if stats are enabled
  const popularCategories = showStats ? getPopularCategories([], 5) : [];

  // Handle expand/collapse
  const handleExpand = (categoryValue) => {
    const newExpanded = localExpanded.includes(categoryValue) ?
    localExpanded.filter((c) => c !== categoryValue) :
    [...localExpanded, categoryValue];

    setLocalExpanded(newExpanded);
    onExpandToggle?.(newExpanded);
  };

  // Handle category selection
  const handleCategorySelect = (categoryValue, subcategoryValue = null) => {
    onCategorySelect?.(categoryValue, subcategoryValue);
  };

  // Filter categories based on search
  const filteredCategories = categoryTree.filter((category) => {
    if (!searchTerm) {return true;}

    const searchLower = searchTerm.toLowerCase();
    return (
      category.label.toLowerCase().includes(searchLower) ||
      category.description?.toLowerCase().includes(searchLower) ||
      category.subcategories && Object.values(category.subcategories).some((sub) =>
      sub.label.toLowerCase().includes(searchLower)
      ));

  });

  // Recursive component for rendering category tree
  const CategoryNode = ({ category, level = 0 }) => {
    const isExpanded = localExpanded.includes(category.value);
    const isSelected = selectedCategory === category.value;
    const hasSubcategories = category.children && category.children.length > 0;

    return (
      <div className="w-full">
        {/* Category Header */}
        <motion.div
          variants={fadeIn}
          className={cn(
            "group relative",
            compact ? "mb-1" : "mb-2"
          )}>

          <div
            onClick={() => handleExpand(category.value)}
            className={cn(
              "flex items-center justify-between w-full p-2 rounded-lg cursor-pointer transition-all",
              compact ?
              "hover:bg-surface-100" :
              "hover:bg-surface-100/50",
              isSelected && "bg-primary/10 border border-primary/20",
              level > 0 && "ml-4"
            )}>

            <div className="flex items-center gap-2 flex-1 min-w-0">
              {/* Expand/Collapse Icon */}
              {hasSubcategories &&
              <motion.div
                animate={{ rotate: isExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
                className="flex-shrink-0">

                  <ChevronRight className="w-4 h-4 text-slate-500" />
              </motion.div>
              }

              {/* Category Icon */}
              <div className={cn(
                "flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs",
                category.color,
                !hasSubcategories && "opacity-60"
              )}>
                {category.icon}
              </div>

              {/* Category Name */}
              <div className="min-w-0 flex-1">
                <span className={cn(
                  "text-sm font-medium truncate",
                  isSelected ? "text-primary" : "text-slate-300"
                )}>
                  {category.label}
                </span>
                {showStats &&
                <Badge variant="secondary" className="text-xs ml-2">
                    {Math.floor(Math.random() * 50) + 10}篇
                </Badge>
                }
              </div>
            </div>

            {/* Actions */}
            {!compact &&
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCategorySelect(category.value);
                }}>

                  <BookOpen className="w-3 h-3" />
                </Button>
                {hasSubcategories &&
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  handleExpand(category.value);
                }}>

                    <ChevronDown className="w-3 h-3" />
              </Button>
              }
            </div>
            }
          </div>

          {/* Category Description */}
          {!compact && category.description &&
          <p className="text-xs text-slate-400 mt-1 ml-8">
              {category.description}
          </p>
          }
        </motion.div>

        {/* Subcategories */}
        <AnimatePresence>
          {isExpanded && hasSubcategories &&
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="ml-4 mt-1">

              {category.children.map((subcategory) =>
            <CategoryNode
              key={subcategory.value}
              category={subcategory}
              level={level + 1} />

            )}
          </motion.div>
          }
        </AnimatePresence>
      </div>);

  };

  return (
    <div className={cn(
      "w-full",
      variant === "sidebar" && "bg-surface-50/50 rounded-lg p-3",
      variant === "embedded" && "p-2"
    )}>
      {/* Search Bar */}
      {showSearch &&
      <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
            type="text"
            placeholder="搜索分类..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-surface-50 border border-white/10 rounded-lg text-sm text-white placeholder-slate-400 focus:outline-none focus:border-primary/30 focus:ring-1 focus:ring-primary/20" />

          </div>
      </div>
      }

      {/* Categories List */}
      <div className="space-y-1">
        {filteredCategories.map((category) =>
        <CategoryNode key={category.value} category={category} />
        )}
      </div>

      {/* Popular Categories */}
      {!compact && showStats && popularCategories.length > 0 && searchTerm === "" &&
      <div className="mt-4 pt-4 border-t border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-slate-400" />
            <span className="text-xs font-medium text-slate-400">热门分类</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {popularCategories.map(({ category, count }) =>
          <Badge
            key={category}
            variant="secondary"
            className="text-xs cursor-pointer hover:bg-primary/10"
            onClick={() => handleCategorySelect(category)}>

                {formatCategory(category)}
                <span className="ml-1 text-slate-500">({count})</span>
          </Badge>
          )}
          </div>
      </div>
      }

      {/* Add Category Button */}
      {!compact &&
      <div className="mt-4 pt-4 border-t border-white/10">
          <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => {


            // Handle add category
          }}>
            <Plus className="w-4 h-4 mr-2" />
            添加分类
          </Button>
      </div>}
    </div>);

}

// Compact Category Selector Component
export function CategorySelector({
  categories = null,
  selectedCategory = null,
  selectedSubcategory = null,
  onCategorySelect: _onCategorySelect,
  placeholder = "选择分类",
  showSubcategories = true,
  variant: _variant = "default"
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const categoryTree = categories || generateCategoryTree();

  const handleCategorySelect = (categoryValue, subcategoryValue = null) => {
    _onCategorySelect?.(categoryValue, subcategoryValue);
  };

  const selectedCategoryConfig = selectedCategory ?
  getCategoryConfig(selectedCategory) :
  null;

  const filteredCategories = categoryTree.filter((category) => {
    if (!searchTerm) {return true;}
    const searchLower = searchTerm.toLowerCase();
    return (
      category.label.toLowerCase().includes(searchLower) ||
      category.subcategories && Object.values(category.subcategories).some((sub) =>
      sub.label.toLowerCase().includes(searchLower)
      ));

  });

  return (
    <div className="relative w-full">
      {/* Trigger */}
      <Button
        variant="outline"
        className="w-full justify-between"
        onClick={() => setIsOpen(!isOpen)}>

        <div className="flex items-center gap-2">
          {selectedCategoryConfig ?
          <>
              <div className={cn(
              "w-5 h-5 rounded flex items-center justify-center text-xs",
              selectedCategoryConfig.color
            )}>
                {selectedCategoryConfig.icon}
              </div>
              <span>{formatCategory(selectedCategory)}</span>
              {selectedSubcategory &&
            <span className="text-slate-400">/ {selectedSubcategory}</span>
            }
          </> :

          <span className="text-slate-400">{placeholder}</span>
          }
        </div>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {/* Dropdown */}
      <AnimatePresence>
        {isOpen &&
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className="absolute top-full left-0 right-0 mt-2 bg-surface-100 border border-white/10 rounded-lg shadow-lg z-50 max-h-60 overflow-hidden">

            {/* Search */}
            <div className="p-2 border-b border-white/10">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-slate-400" />
                <input
                type="text"
                placeholder="搜索分类..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-2 py-1 bg-surface-50 border border-white/10 rounded text-xs text-white placeholder-slate-400 focus:outline-none focus:border-primary/30" />

              </div>
            </div>

            {/* Categories */}
            <div className="max-h-48 overflow-y-auto">
              {filteredCategories.map((category) =>
            <div key={category.value}>
                  {/* Category */}
                  <div
                className="flex items-center gap-2 p-2 hover:bg-surface-50/50 cursor-pointer"
                onClick={() => {
                  if (!showSubcategories || !category.children?.length) {
                    handleCategorySelect(category.value);
                    setIsOpen(false);
                  } else {
                    handleCategorySelect(category.value);
                  }
                }}>

                    <div className={cn(
                  "w-4 h-4 rounded flex items-center justify-center text-xs",
                  category.color
                )}>
                      {category.icon}
                    </div>
                    <span className="text-sm text-white">{category.label}</span>
                    {category.children?.length > 0 &&
                <ChevronRight className="w-3 h-3 text-slate-400 ml-auto" />
                }
                  </div>

                  {/* Subcategories */}
                  {showSubcategories && selectedCategory === category.value && category.children?.length > 0 &&
              <div className="ml-4 border-l border-white/10">
                      {category.children.map((subcategory) =>
                <div
                  key={subcategory.value}
                  className="flex items-center gap-2 p-2 pl-4 hover:bg-surface-50/50 cursor-pointer"
                  onClick={() => {
                    handleCategorySelect(category.value, subcategory.value);
                    setIsOpen(false);
                  }}>

                          <div className={cn(
                    "w-3 h-3 rounded flex items-center justify-center text-xs",
                    subcategory.color
                  )}>
                            {subcategory.icon}
                          </div>
                          <span className="text-sm text-slate-300">{subcategory.label}</span>
                </div>
                )}
              </div>
              }
            </div>
            )}
            </div>
        </motion.div>
        }
      </AnimatePresence>
    </div>);

}

// Category Filter Pills Component
export function CategoryFilterPills({
  categories = null,
  selectedCategory = null,
  selectedSubcategory = null,
  onCategorySelect,
  removable = true,
  maxDisplay: _maxDisplay = 5
}) {
  const _categoryTree = categories || generateCategoryTree();

  const handleRemoveFilter = (e, category, subcategory) => {
    e.stopPropagation();
    onCategorySelect?.(category, subcategory);
  };

  if (!selectedCategory) {return null;}

  return (
    <div className="flex flex-wrap gap-2">
      <Badge
        variant="secondary"
        className="cursor-pointer hover:bg-primary/10"
        onClick={() => onCategorySelect?.(selectedCategory, null)}>

        {formatCategory(selectedCategory)}
        {selectedSubcategory && ` / ${selectedSubcategory}`}
        {removable &&
        <ChevronUp
          className="w-3 h-3 ml-1 hover:text-red-500"
          onClick={(e) => handleRemoveFilter(e, selectedCategory, selectedSubcategory)} />

        }
      </Badge>
    </div>);

}
