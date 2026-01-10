import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cultureWallApi } from "../../services/api";
import {
  Target,
  Heart,
  AlertCircle,
  Bell,
  Award,
  TrendingUp,
  Calendar,
  CheckCircle2,
  Clock,
  ArrowRight,
  Play,
  Pause,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";
import { Card, CardContent, Badge, Button } from "../ui";
import { cn } from "../../lib/utils";

const contentTypeConfig = {
  STRATEGY: {
    label: "战略规划",
    icon: Target,
    color: "bg-purple-500",
    textColor: "text-purple-700",
    bgColor: "bg-purple-50",
  },
  CULTURE: {
    label: "企业文化",
    icon: Heart,
    color: "bg-red-500",
    textColor: "text-red-700",
    bgColor: "bg-red-50",
  },
  IMPORTANT: {
    label: "重要事项",
    icon: AlertCircle,
    color: "bg-orange-500",
    textColor: "text-orange-700",
    bgColor: "bg-orange-50",
  },
  NOTICE: {
    label: "通知公告",
    icon: Bell,
    color: "bg-blue-500",
    textColor: "text-blue-700",
    bgColor: "bg-blue-50",
  },
  REWARD: {
    label: "奖励通报",
    icon: Award,
    color: "bg-yellow-500",
    textColor: "text-yellow-700",
    bgColor: "bg-yellow-50",
  },
};

const goalTypeConfig = {
  MONTHLY: { label: "月度目标", color: "bg-blue-500" },
  QUARTERLY: { label: "季度目标", color: "bg-green-500" },
};

/**
 * 文化墙滚动播放组件
 * 可在工作台页面中嵌入使用，显示企业战略、企业文化、重要事项、通知公告、奖励通报和个人目标
 *
 * @param {Object} props
 * @param {boolean} props.autoPlay - 是否自动播放，默认true
 * @param {number} props.interval - 自动播放间隔（毫秒），默认5000
 * @param {boolean} props.showControls - 是否显示控制按钮，默认true
 * @param {boolean} props.showIndicators - 是否显示指示器，默认true
 * @param {string} props.height - 组件高度，默认'400px'
 * @param {Function} props.onItemClick - 点击项目时的回调函数
 */
export default function CultureWallCarousel({
  autoPlay = true,
  interval = 5000,
  showControls = true,
  showIndicators = true,
  height = "400px",
  onItemClick,
}) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const autoPlayIntervalRef = useRef(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (isPlaying && data) {
      const allItems = getAllItems();
      if (allItems.length > 1) {
        autoPlayIntervalRef.current = setInterval(() => {
          setCurrentIndex((prev) => (prev + 1) % allItems.length);
        }, interval);
      }
      return () => {
        if (autoPlayIntervalRef.current) {
          clearInterval(autoPlayIntervalRef.current);
        }
      };
    } else if (autoPlayIntervalRef.current) {
      clearInterval(autoPlayIntervalRef.current);
    }
  }, [isPlaying, data, interval]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await cultureWallApi.summary.get();
      const summaryData = res.data || res;
      setData(summaryData);
    } catch (err) {
      console.error("Failed to fetch culture wall data:", err);
    } finally {
      setLoading(false);
    }
  };

  const getAllItems = () => {
    if (!data) return [];
    const items = [];

    // 添加各类内容（管理员设置的内容）
    data.strategies?.forEach((item) =>
      items.push({ ...item, category: "STRATEGY" }),
    );
    data.cultures?.forEach((item) =>
      items.push({ ...item, category: "CULTURE" }),
    );
    data.important_items?.forEach((item) =>
      items.push({ ...item, category: "IMPORTANT" }),
    );
    data.notices?.forEach((item) =>
      items.push({ ...item, category: "NOTICE" }),
    );
    data.rewards?.forEach((item) =>
      items.push({ ...item, category: "REWARD" }),
    );

    // 添加个人目标（如果管理员允许显示）
    // 注意：如果后端返回的personal_goals为空数组，表示管理员禁用了个人目标显示
    // 如果返回了数据，则表示允许显示
    if (data.personal_goals && data.personal_goals.length > 0) {
      data.personal_goals.forEach((item) =>
        items.push({ ...item, category: "GOAL" }),
      );
    }

    // 添加系统通知
    data.notifications?.forEach((item) =>
      items.push({ ...item, category: "NOTIFICATION" }),
    );

    return items;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    });
  };

  const renderContentItem = (item) => {
    const config = contentTypeConfig[item.content_type || item.category];
    if (!config) return null;

    const Icon = config.icon;

    return (
      <motion.div
        key={item.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className={cn("h-full flex flex-col cursor-pointer", config.bgColor)}
        onClick={() => onItemClick && onItemClick(item)}
      >
        <Card className="h-full border-0 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-4 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <div className={cn("p-1.5 rounded-lg text-white", config.color)}>
                <Icon className="w-4 h-4" />
              </div>
              <Badge className={cn("text-xs", config.color)}>
                {config.label}
              </Badge>
              {item.publish_date && (
                <span className="ml-2 text-xs text-gray-500">
                  {formatDate(item.publish_date)}
                </span>
              )}
              {item.is_read && (
                <CheckCircle2 className="w-3 h-3 text-green-500 ml-auto" />
              )}
            </div>

            <h3 className="text-lg font-bold mb-2 line-clamp-2">
              {item.title}
            </h3>

            {item.summary && (
              <p className="text-sm text-gray-600 mb-3 flex-1 line-clamp-3">
                {item.summary}
              </p>
            )}

            {item.content && !item.summary && (
              <p className="text-sm text-gray-600 mb-3 flex-1 line-clamp-3">
                {item.content.substring(0, 150)}
                {item.content.length > 150 && "..."}
              </p>
            )}

            {item.images && item.images.length > 0 && (
              <div className="mb-3">
                <img
                  src={item.images[0].url}
                  alt={item.images[0].alt || item.title}
                  className="w-full h-32 object-cover rounded-lg"
                />
              </div>
            )}

            <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-200">
              {item.published_by_name && (
                <span className="text-xs text-gray-500">
                  {item.published_by_name}
                </span>
              )}
              <Button variant="ghost" size="sm" className="h-6 text-xs">
                查看详情 <ArrowRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const renderGoalItem = (goal) => {
    const config = goalTypeConfig[goal.goal_type];
    const progress = goal.progress || 0;
    const isCompleted = goal.status === "COMPLETED";

    return (
      <motion.div
        key={goal.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="h-full cursor-pointer"
        onClick={() => onItemClick && onItemClick(goal)}
      >
        <Card className="h-full border-2 border-blue-200 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-4 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <div className={cn("p-1.5 rounded-lg text-white", config.color)}>
                <TrendingUp className="w-4 h-4" />
              </div>
              <Badge className={cn("text-xs", config.color)}>
                {config.label}
              </Badge>
              <span className="ml-2 text-xs text-gray-500">{goal.period}</span>
              {isCompleted && (
                <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />
              )}
            </div>

            <h3 className="text-lg font-bold mb-2 line-clamp-2">
              {goal.title}
            </h3>

            {goal.description && (
              <p className="text-sm text-gray-600 mb-3 flex-1 line-clamp-2">
                {goal.description}
              </p>
            )}

            {goal.target_value && (
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="text-gray-600">目标进度</span>
                  <span className="font-medium">
                    {goal.current_value || 0} / {goal.target_value}{" "}
                    {goal.unit || ""}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={cn(
                      "h-2 rounded-full transition-all",
                      isCompleted ? "bg-green-500" : "bg-blue-500",
                    )}
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="text-right text-xs text-gray-500 mt-1">
                  {progress}%
                </div>
              </div>
            )}

            {goal.end_date && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-auto pt-3 border-t border-gray-200">
                <Clock className="w-3 h-3" />
                <span>截止: {formatDate(goal.end_date)}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const renderNotificationItem = (notification) => {
    return (
      <motion.div
        key={notification.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="h-full cursor-pointer"
        onClick={() => onItemClick && onItemClick(notification)}
      >
        <Card className="h-full border-2 border-blue-200 shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="p-4 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-blue-500 text-white">
                <Bell className="w-4 h-4" />
              </div>
              <Badge className="bg-blue-500 text-xs">系统通知</Badge>
            </div>

            <h3 className="text-lg font-bold mb-2 line-clamp-2">
              {notification.title}
            </h3>

            {notification.content && (
              <p className="text-sm text-gray-600 mb-3 flex-1 line-clamp-3">
                {notification.content}
              </p>
            )}

            {notification.created_at && (
              <div className="text-xs text-gray-500 mt-auto pt-3 border-t border-gray-200">
                {formatDate(notification.created_at)}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const renderItem = (item) => {
    if (item.category === "GOAL") {
      return renderGoalItem(item);
    } else if (item.category === "NOTIFICATION") {
      return renderNotificationItem(item);
    } else {
      return renderContentItem(item);
    }
  };

  const allItems = getAllItems();

  if (loading) {
    return (
      <Card style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">加载中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || allItems.length === 0) {
    return (
      <Card style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <Target className="w-12 h-12 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600">暂无内容</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden" style={{ height }}>
      <CardContent className="p-0 h-full relative">
        {/* 控制栏 */}
        {showControls && (
          <div className="absolute top-2 right-2 z-10 flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPlaying(!isPlaying)}
              className="bg-white/90 backdrop-blur-sm h-7 text-xs"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-3 h-3 mr-1" />
                  暂停
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 mr-1" />
                  播放
                </>
              )}
            </Button>
            <div className="bg-white/90 backdrop-blur-sm px-2 py-1 rounded text-xs">
              {currentIndex + 1} / {allItems.length}
            </div>
          </div>
        )}

        {/* 主要内容区域 */}
        <div className="h-full w-full p-4">
          <AnimatePresence mode="wait">
            {allItems[currentIndex] && (
              <motion.div
                key={currentIndex}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="h-full"
              >
                {renderItem(allItems[currentIndex])}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 导航按钮 */}
        {allItems.length > 1 && (
          <>
            <button
              onClick={() =>
                setCurrentIndex(
                  (prev) => (prev - 1 + allItems.length) % allItems.length,
                )
              }
              className="absolute left-2 top-1/2 transform -translate-y-1/2 z-10 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() =>
                setCurrentIndex((prev) => (prev + 1) % allItems.length)
              }
              className="absolute right-2 top-1/2 transform -translate-y-1/2 z-10 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-md hover:bg-white transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </>
        )}

        {/* 指示器 */}
        {showIndicators && allItems.length > 1 && (
          <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 z-10 flex gap-1.5">
            {allItems.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  index === currentIndex
                    ? "bg-blue-600 w-6"
                    : "bg-gray-300 w-1.5",
                )}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
