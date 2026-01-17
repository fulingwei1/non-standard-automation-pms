/**
 * Advantage Products Component - 公司优势产品展示
 * 用于销售模块展示公司主推产品，帮助销售人员快速选择产品
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Package,
  ChevronDown,
  ChevronRight,
  Search,
  Star,
  Zap,
  Car,
  Battery,
  Cpu,
  Wrench,
  Factory,
  Settings,
  GraduationCap,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Copy,
  ExternalLink } from
"lucide-react";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { advantageProductApi } from "../../services/api";

// 类别图标映射
const CATEGORY_ICONS = {
  HOME_APPLIANCE: Zap,
  AUTOMOTIVE: Car,
  NEW_ENERGY: Battery,
  SEMICONDUCTOR: Cpu,
  POWER_TOOLS: Wrench,
  AUTOMATION_LINE: Factory,
  OTHER_EQUIPMENT: Settings,
  EDUCATION: GraduationCap
};

// 类别颜色映射
const CATEGORY_COLORS = {
  HOME_APPLIANCE: "from-blue-500 to-cyan-500",
  AUTOMOTIVE: "from-violet-500 to-purple-500",
  NEW_ENERGY: "from-green-500 to-emerald-500",
  SEMICONDUCTOR: "from-amber-500 to-orange-500",
  POWER_TOOLS: "from-red-500 to-rose-500",
  AUTOMATION_LINE: "from-indigo-500 to-blue-500",
  OTHER_EQUIPMENT: "from-slate-500 to-gray-500",
  EDUCATION: "from-pink-500 to-fuchsia-500"
};

// 类别背景色
const CATEGORY_BG = {
  HOME_APPLIANCE: "bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20",
  AUTOMOTIVE: "bg-violet-500/10 border-violet-500/20 hover:bg-violet-500/20",
  NEW_ENERGY: "bg-green-500/10 border-green-500/20 hover:bg-green-500/20",
  SEMICONDUCTOR: "bg-amber-500/10 border-amber-500/20 hover:bg-amber-500/20",
  POWER_TOOLS: "bg-red-500/10 border-red-500/20 hover:bg-red-500/20",
  AUTOMATION_LINE:
  "bg-indigo-500/10 border-indigo-500/20 hover:bg-indigo-500/20",
  OTHER_EQUIPMENT: "bg-slate-500/10 border-slate-500/20 hover:bg-slate-500/20",
  EDUCATION: "bg-pink-500/10 border-pink-500/20 hover:bg-pink-500/20"
};

// 单个类别展示组件
function CategorySection({
  category,
  products,
  isExpanded,
  onToggle,
  onProductSelect
}) {
  const IconComponent = CATEGORY_ICONS[category.code] || Package;
  const colorClass =
  CATEGORY_COLORS[category.code] || "from-slate-500 to-gray-500";
  const bgClass =
  CATEGORY_BG[category.code] || "bg-slate-500/10 border-slate-500/20";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-3">

      {/* 类别标题 */}
      <button
        onClick={onToggle}
        className={cn(
          "w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200",
          bgClass
        )}>

        <div className="flex items-center gap-3">
          <div className={cn("p-2 rounded-lg bg-gradient-to-br", colorClass)}>
            <IconComponent className="w-4 h-4 text-white" />
          </div>
          <div className="text-left">
            <h4 className="font-medium text-white">{category.name}</h4>
            <p className="text-xs text-slate-400">{products.length} 个产品</p>
          </div>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}>

          <ChevronDown className="w-5 h-5 text-slate-400" />
        </motion.div>
      </button>

      {/* 产品列表 */}
      <AnimatePresence>
        {isExpanded &&
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden">

            <div className="mt-2 pl-4 space-y-1">
              {products.map((product, index) =>
            <motion.div
              key={product.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.03 }}
              onClick={() => onProductSelect?.(product)}
              className={cn(
                "flex items-center justify-between p-2 rounded-md cursor-pointer",
                "bg-surface-50/50 hover:bg-surface-100 border border-transparent hover:border-white/10",
                "transition-all duration-150 group"
              )}>

                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-mono text-slate-500 w-16 flex-shrink-0">
                      {product.product_code}
                    </span>
                    <span className="text-sm text-slate-300 truncate group-hover:text-white transition-colors">
                      {product.product_name}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                  onClick={(e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(product.product_name);
                  }}
                  className="p-1 hover:bg-white/10 rounded"
                  title="复制产品名称">

                      <Copy className="w-3 h-3 text-slate-400" />
                    </button>
                  </div>
                </motion.div>
            )}
            </div>
          </motion.div>
        }
      </AnimatePresence>
    </motion.div>);

}

// 搜索结果高亮
function HighlightedProduct({ product, searchTerm, onSelect }) {
  const highlightText = (text, term) => {
    if (!term) return text;
    const parts = text.split(new RegExp(`(${term})`, "gi"));
    return parts.map((part, i) =>
    part.toLowerCase() === term.toLowerCase() ?
    <span key={i} className="bg-yellow-500/30 text-yellow-300">
          {part}
        </span> :

    part

    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      onClick={() => onSelect?.(product)}
      className={cn(
        "flex items-center justify-between p-3 rounded-lg cursor-pointer",
        "bg-surface-50 hover:bg-surface-100 border border-white/5 hover:border-white/10",
        "transition-all duration-150"
      )}>

      <div className="flex items-center gap-3">
        <div className="p-1.5 rounded bg-primary-500/10">
          <Star className="w-4 h-4 text-primary-400" />
        </div>
        <div>
          <div className="text-sm text-white">
            {highlightText(product.product_name, searchTerm)}
          </div>
          <div className="text-xs text-slate-500">
            {product.product_code} · {product.category_name}
          </div>
        </div>
      </div>
      <CheckCircle2 className="w-4 h-4 text-green-400" />
    </motion.div>);

}

// 主组件
export default function AdvantageProducts({
  onProductSelect,
  selectedProduct: _selectedProduct,
  compact = false,
  showSearch = true,
  maxHeight = "500px"
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groupedData, setGroupedData] = useState([]);
  const [expandedCategories, setExpandedCategories] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState([]);

  // 加载数据
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await advantageProductApi.getProductsGrouped();
      setGroupedData(response.data || []);
      // 默认展开第一个类别
      if (response.data?.length > 0) {
        setExpandedCategories(new Set([response.data[0].category.code]));
      }
    } catch (err) {
      console.error("Failed to load advantage products:", err);
      setError("加载产品数据失败");
      // 使用 mock 数据
      setGroupedData(getMockData());
    } finally {
      setLoading(false);
    }
  };

  // 搜索处理
  useEffect(() => {
    if (!searchTerm.trim()) {
      setSearchResults([]);
      return;
    }

    const term = searchTerm.toLowerCase();
    const results = [];
    groupedData.forEach((group) => {
      group.products.forEach((product) => {
        if (
        product.product_name.toLowerCase().includes(term) ||
        product.product_code.toLowerCase().includes(term))
        {
          results.push(product);
        }
      });
    });
    setSearchResults(results.slice(0, 10));
  }, [searchTerm, groupedData]);

  // 切换类别展开状态
  const toggleCategory = (code) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(code)) {
        next.delete(code);
      } else {
        next.add(code);
      }
      return next;
    });
  };

  // 全部展开/收起
  const toggleAll = () => {
    if (expandedCategories.size === groupedData.length) {
      setExpandedCategories(new Set());
    } else {
      setExpandedCategories(new Set(groupedData.map((g) => g.category.code)));
    }
  };

  // 统计信息
  const totalProducts = groupedData.reduce(
    (sum, g) => sum + g.products.length,
    0
  );
  const totalCategories = groupedData.length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-primary-400 animate-spin" />
        <span className="ml-2 text-slate-400">加载优势产品...</span>
      </div>);

  }

  return (
    <motion.div variants={fadeIn} className="space-y-4">
      {/* 头部统计 */}
      {!compact &&
      <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-primary-400" />
              <span className="text-sm text-slate-400">
                {totalCategories} 个类别 · {totalProducts} 个产品
              </span>
            </div>
          </div>
          <button
          onClick={toggleAll}
          className="text-xs text-primary-400 hover:text-primary-300 transition-colors">

            {expandedCategories.size === groupedData.length ?
          "全部收起" :
          "全部展开"}
          </button>
        </div>
      }

      {/* 搜索框 */}
      {showSearch &&
      <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="搜索产品名称或编码..."
          className={cn(
            "w-full pl-10 pr-4 py-2 rounded-lg",
            "bg-surface-50 border border-white/10",
            "text-sm text-white placeholder:text-slate-500",
            "focus:outline-none focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/20",
            "transition-all duration-200"
          )} />

        </div>
      }

      {/* 搜索结果 */}
      {searchTerm && searchResults.length > 0 &&
      <div className="space-y-2">
          <div className="text-xs text-slate-500">
            找到 {searchResults.length} 个匹配产品
          </div>
          {searchResults.map((product) =>
        <HighlightedProduct
          key={product.id}
          product={product}
          searchTerm={searchTerm}
          onSelect={onProductSelect} />

        )}
        </div>
      }

      {/* 无搜索结果 */}
      {searchTerm && searchResults.length === 0 &&
      <div className="text-center py-4 text-slate-500">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">未找到匹配的产品</p>
        </div>
      }

      {/* 分类列表 */}
      {!searchTerm &&
      <div className="space-y-1 overflow-y-auto pr-1" style={{ maxHeight }}>
          {groupedData.map((group) =>
        <CategorySection
          key={group.category.code}
          category={group.category}
          products={group.products}
          isExpanded={expandedCategories.has(group.category.code)}
          onToggle={() => toggleCategory(group.category.code)}
          onProductSelect={onProductSelect} />

        )}
        </div>
      }

      {/* 错误提示 */}
      {error &&
      <div className="text-center py-2 text-amber-400 text-xs">
          {error}（显示演示数据）
        </div>
      }
    </motion.div>);

}

// Mock 数据
function getMockData() {
  return [
  {
    category: {
      id: 1,
      code: "HOME_APPLIANCE",
      name: "白色家电",
      product_count: 19
    },
    products: [
    {
      id: 1,
      product_code: "KC2701",
      product_name: "离线双工位FCT",
      category_name: "白色家电"
    },
    {
      id: 2,
      product_code: "KC2702",
      product_name: "离线显示双工位FCT",
      category_name: "白色家电"
    },
    {
      id: 3,
      product_code: "KC2706",
      product_name: "在线式双轨双工位FCT",
      category_name: "白色家电"
    }]

  },
  {
    category: {
      id: 2,
      code: "AUTOMOTIVE",
      name: "汽车电子",
      product_count: 34
    },
    products: [
    {
      id: 4,
      product_code: "KC2101",
      product_name: "域控制器测试系统",
      category_name: "汽车电子"
    },
    {
      id: 5,
      product_code: "KC2102",
      product_name: "车载导航整机测试系统",
      category_name: "汽车电子"
    },
    {
      id: 6,
      product_code: "KC2106",
      product_name: "电机控制器测试系统",
      category_name: "汽车电子"
    }]

  },
  {
    category: {
      id: 3,
      code: "NEW_ENERGY",
      name: "新能源",
      product_count: 24
    },
    products: [
    {
      id: 7,
      product_code: "KC2901",
      product_name: "PACK/模组EOL测试系统",
      category_name: "新能源"
    },
    {
      id: 8,
      product_code: "KC2909",
      product_name: "BMS测试系统",
      category_name: "新能源"
    }]

  },
  {
    category: {
      id: 4,
      code: "SEMICONDUCTOR",
      name: "半导体",
      product_count: 12
    },
    products: [
    {
      id: 9,
      product_code: "KC3105",
      product_name: "功率器件老化测试设备",
      category_name: "半导体"
    },
    {
      id: 10,
      product_code: "KC3107",
      product_name: "功率器件ATE测试设备",
      category_name: "半导体"
    }]

  }];

}

// 紧凑版本 - 用于下拉选择
export function AdvantageProductSelect({
  value,
  onChange,
  placeholder = "选择优势产品"
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && products.length === 0) {
      loadProducts();
    }
  }, [isOpen]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await advantageProductApi.getProductsSimple();
      setProducts(response.data || []);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === value);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "w-full flex items-center justify-between px-3 py-2 rounded-lg",
          "bg-surface-50 border border-white/10 text-left",
          "hover:border-white/20 transition-colors",
          isOpen && "border-primary-500/50 ring-1 ring-primary-500/20"
        )}>

        <span
          className={cn(
            "text-sm",
            selectedProduct ? "text-white" : "text-slate-500"
          )}>

          {selectedProduct ? selectedProduct.product_name : placeholder}
        </span>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-slate-400 transition-transform",
            isOpen && "rotate-180"
          )} />

      </button>

      <AnimatePresence>
        {isOpen &&
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          className={cn(
            "absolute z-50 w-full mt-1 py-1 rounded-lg",
            "bg-surface-100 border border-white/10 shadow-xl",
            "max-h-60 overflow-y-auto"
          )}>

            {loading ?
          <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin text-primary-400" />
              </div> :

          products.map((product) =>
          <button
            key={product.id}
            type="button"
            onClick={() => {
              onChange(product.id, product);
              setIsOpen(false);
            }}
            className={cn(
              "w-full px-3 py-2 text-left text-sm",
              "hover:bg-white/5 transition-colors",
              value === product.id ?
              "text-primary-400 bg-primary-500/10" :
              "text-slate-300"
            )}>

                  <span className="font-mono text-xs text-slate-500 mr-2">
                    {product.product_code}
                  </span>
                  {product.product_name}
                </button>
          )
          }
          </motion.div>
        }
      </AnimatePresence>
    </div>);

}