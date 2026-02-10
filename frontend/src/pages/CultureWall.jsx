import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cultureWallApi } from "../services/api";
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
} from "lucide-react";
import { Card, CardContent, Badge, Button } from "../components/ui";
import { cn } from "../lib/utils";
import { formatDate } from "../lib/formatters";

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

export default function CultureWall() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [autoPlayInterval, setAutoPlayInterval] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (isPlaying && data) {
      const interval = setInterval(() => {
        setCurrentIndex((prev) => {
          const allItems = getAllItems();
          return (prev + 1) % allItems.length;
        });
      }, 5000); // 每5秒切换一次
      setAutoPlayInterval(interval);
      return () => clearInterval(interval);
    } else if (autoPlayInterval) {
      clearInterval(autoPlayInterval);
    }
  }, [isPlaying, data]);

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
    if (!data) {return [];}
    const items = [];

    // 添加各类内容
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
    data.personal_goals?.forEach((item) =>
      items.push({ ...item, category: "GOAL" }),
    );
    data.notifications?.forEach((item) =>
      items.push({ ...item, category: "NOTIFICATION" }),
    );

    return items;
  };

  const renderContentItem = (item) => {
    const config = contentTypeConfig[item.content_type || item.category];
    if (!config) {return null;}

    const Icon = config.icon;

    return (
      <motion.div
        key={item.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={cn("h-full flex flex-col", config.bgColor)}
      >
        <Card className="h-full border-0 shadow-lg">
          <CardContent className="p-6 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className={cn("p-2 rounded-lg text-white", config.color)}>
                <Icon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <Badge className={config.color}>{config.label}</Badge>
                {item.publish_date && (
                  <span className="ml-2 text-sm text-gray-500">
                    {formatDate(item.publish_date)}
                  </span>
                )}
              </div>
              {item.is_read && (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              )}
            </div>

            <h3 className="text-xl font-bold mb-3">{item.title}</h3>

            {item.summary && (
              <p className="text-gray-600 mb-4 flex-1">{item.summary}</p>
            )}

            {item.content && (
              <div className="text-sm text-gray-500 mb-4 line-clamp-3">
                {item.content.substring(0, 200)}
                {item.content.length > 200 && "..."}
              </div>
            )}

            {item.images && item.images.length > 0 && (
              <div className="mb-4">
                <img
                  src={item.images[0].url}
                  alt={item.images[0].alt || item.title}
                  className="w-full h-48 object-cover rounded-lg"
                />
              </div>
            )}

            <div className="flex items-center justify-between mt-auto pt-4 border-t">
              {item.published_by_name && (
                <span className="text-sm text-gray-500">
                  发布人: {item.published_by_name}
                </span>
              )}
              <Button variant="ghost" size="sm">
                查看详情 <ArrowRight className="w-4 h-4 ml-1" />
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
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="h-full"
      >
        <Card className="h-full border-2 border-blue-200 shadow-lg">
          <CardContent className="p-6 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className={cn("p-2 rounded-lg text-white", config.color)}>
                <TrendingUp className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <Badge className={config.color}>{config.label}</Badge>
                <span className="ml-2 text-sm text-gray-500">
                  {goal.period}
                </span>
              </div>
              {isCompleted && (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              )}
            </div>

            <h3 className="text-xl font-bold mb-3">{goal.title}</h3>

            {goal.description && (
              <p className="text-gray-600 mb-4 flex-1">{goal.description}</p>
            )}

            {goal.target_value && (
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-600">目标进度</span>
                  <span className="font-medium">
                    {goal.current_value || 0} / {goal.target_value}{" "}
                    {goal.unit || ""}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={cn(
                      "h-3 rounded-full transition-all",
                      isCompleted ? "bg-green-500" : "bg-blue-500",
                    )}
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="text-right text-sm text-gray-500 mt-1">
                  {progress}%
                </div>
              </div>
            )}

            {goal.end_date && (
              <div className="flex items-center gap-2 text-sm text-gray-500 mt-auto pt-4 border-t">
                <Clock className="w-4 h-4" />
                <span>截止日期: {formatDate(goal.end_date)}</span>
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
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="h-full"
      >
        <Card className="h-full border-2 border-blue-200 shadow-lg">
          <CardContent className="p-6 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-blue-500 text-white">
                <Bell className="w-5 h-5" />
              </div>
              <Badge className="bg-blue-500">系统通知</Badge>
            </div>

            <h3 className="text-xl font-bold mb-3">{notification.title}</h3>

            {notification.content && (
              <p className="text-gray-600 mb-4 flex-1">
                {notification.content}
              </p>
            )}

            {notification.created_at && (
              <div className="text-sm text-gray-500 mt-auto pt-4 border-t">
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
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (!data || allItems.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">暂无内容</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* 控制栏 */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsPlaying(!isPlaying)}
          className="bg-white/90 backdrop-blur-sm"
        >
          {isPlaying ? (
            <>
              <Pause className="w-4 h-4 mr-1" />
              暂停
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-1" />
              播放
            </>
          )}
        </Button>
        <div className="bg-white/90 backdrop-blur-sm px-3 py-1 rounded-md text-sm">
          {currentIndex + 1} / {allItems.length}
        </div>
      </div>

      {/* 指示器 */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10 flex gap-2">
        {allItems.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentIndex(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-all",
              index === currentIndex ? "bg-blue-600 w-8" : "bg-gray-300",
            )}
          />
        ))}
      </div>

      {/* 主要内容区域 */}
      <div
        ref={containerRef}
        className="h-full w-full flex items-center justify-center p-8"
      >
        <AnimatePresence mode="wait">
          {allItems[currentIndex] && (
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.5 }}
              className="w-full max-w-4xl h-full max-h-[80vh]"
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
            className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 p-3 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-white transition-colors"
          >
            <ArrowRight className="w-6 h-6 rotate-180" />
          </button>
          <button
            onClick={() =>
              setCurrentIndex((prev) => (prev + 1) % allItems.length)
            }
            className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 p-3 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:bg-white transition-colors"
          >
            <ArrowRight className="w-6 h-6" />
          </button>
        </>
      )}
    </div>
  );
}
