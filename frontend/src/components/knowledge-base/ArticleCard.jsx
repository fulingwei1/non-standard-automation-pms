/**
 * Article Card Component - Displays knowledge base articles in card format
 */

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/formatters";
import { fadeIn, scaleIn } from "../../lib/animations";
import {
  FileText,
  Clock,
  Eye,
  User,
  Tag,
  Bookmark,
  Share2,
  MoreHorizontal,
  Star,
  TrendingUp,
  ChevronRight,
  Calendar,
  MessageCircle,
  ThumbsUp,
  File,
  ExternalLink,
  Download } from
"lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  articleCategoryConfigs as _articleCategoryConfigs,
  articleStatusConfigs as _articleStatusConfigs,
  articlePriorityConfigs as _articlePriorityConfigs,
  articleTypeConfigs,
  getCategoryConfig,
  formatCategory,
  formatStatus,
  formatPriority,
  formatType,
  getCategoryColor,
  getPriorityConfig,
  getStatusConfig } from
"@/lib/constants/knowledge";

export default function ArticleCard({
  article,
  onClick,
  compact = false,
  showActions = true,
  variant = "default"
}) {
  const {
    id: _id,
    title,
    summary,
    content,
    category,
    subcategory,
    status = "DRAFT",
    priority = "MEDIUM",
    type = "KNOWLEDGE_BASE",
    author = "系统管理员",
    authorAvatar: _authorAvatar,
    createdDate: _createdDate,
    updatedDate,
    views = 0,
    likes = 0,
    tags = [],
    readTime,
    featured = false,
    popular = false,
    bookmarked = false,
    attachments = [],
    thumbnail: _thumbnail,
    metadata: _metadata = {}
  } = article;

  const categoryConfig = getCategoryConfig(category);
  const priorityConfig = getPriorityConfig(priority);
  const statusConfig = getStatusConfig(status);
  const _typeConfig = articleTypeConfigs[type];

  // 计算阅读时间
  const calculatedReadTime = readTime || Math.ceil(content.length / 500);

  if (compact) {
    return (
      <motion.div
        variants={fadeIn}
        onClick={() => onClick?.(article)}
        className={cn(
          "flex items-center justify-between p-3 bg-surface-50 rounded-lg hover:bg-surface-100 cursor-pointer transition-colors group",
          status === "PUBLISHED" ? "hover:border-primary/30" : "opacity-70"
        )}>

        <div className="flex items-center gap-3 flex-1">
          <div className="flex-shrink-0">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center text-sm",
              getCategoryColor(category)
            )}>
              {categoryConfig?.icon || "📄"}
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-white truncate">
                {title}
              </h4>
              {featured && <Star className="w-4 h-4 text-amber-500 flex-shrink-0" />}
              {popular && <TrendingUp className="w-4 h-4 text-blue-500 flex-shrink-0" />}
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {author}
              </span>
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {views}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {calculatedReadTime}min
              </span>
            </div>
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white transition-colors flex-shrink-0" />
      </motion.div>);

  }

  return (
    <motion.div
      variants={scaleIn}
      initial="hidden"
      animate="visible"
      onClick={() => onClick?.(article)}
      className={cn(
        "bg-surface-100/50 backdrop-blur-sm rounded-xl border overflow-hidden",
        "hover:shadow-lg hover:shadow-primary/5 cursor-pointer transition-all",
        status === "PUBLISHED" ?
        "border-white/5 hover:border-primary/30" :
        "border-slate-500/20 opacity-70",
        featured && "ring-2 ring-amber-500/30",
        variant === "highlight" && "border-primary/50"
      )}>

      {/* Header */}
      <div className="p-4">
        {/* Category and Status */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center text-lg",
              getCategoryColor(category)
            )}>
              {categoryConfig?.icon || "📄"}
            </div>
            <div>
              <Badge variant="secondary" className="text-xs mb-1">
                {formatCategory(category)}
                {subcategory && ` / ${subcategory}`}
              </Badge>
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className={cn("text-xs", priorityConfig.color.replace("bg-", "bg-").replace("text-", "text-"))}>

                  {formatPriority(priority)}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn("text-xs", statusConfig.color.replace("bg-", "bg-").replace("text-", "text-"))}>

                  {formatStatus(status)}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {formatType(type)}
                </Badge>
              </div>
            </div>
          </div>
          {showActions &&
          <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="w-4 h-4 text-slate-400" />
          </Button>
          }
        </div>

        {/* Title */}
        <div className="mb-3">
          <h3 className="font-semibold text-white mb-1 group-hover:text-primary transition-colors">
            {title}
          </h3>
          {featured &&
          <div className="flex items-center gap-1 mb-2">
              <Star className="w-4 h-4 text-amber-500" />
              <span className="text-xs text-amber-400 font-medium">精选文章</span>
          </div>
          }
          {popular &&
          <div className="flex items-center gap-1 mb-2">
              <TrendingUp className="w-4 h-4 text-blue-500" />
              <span className="text-xs text-blue-400 font-medium">热门文章</span>
          </div>
          }
        </div>

        {/* Summary */}
        {summary &&
        <p className="text-sm text-slate-300 mb-3 line-clamp-2">
            {summary}
        </p>
        }

        {/* Tags */}
        {tags?.length > 0 &&
        <div className="flex flex-wrap gap-1 mb-3">
            {tags.slice(0, 3).map((tag, index) =>
          <Badge key={index} variant="secondary" className="text-xs">
                #{tag}
          </Badge>
          )}
            {tags?.length > 3 &&
          <Badge variant="secondary" className="text-xs">
                +{tags?.length - 3}
          </Badge>
          }
        </div>
        }

        {/* Content Preview */}
        {content &&
        <div className="mb-3 p-3 bg-surface-50/50 rounded-lg">
            <p className="text-xs text-slate-400 line-clamp-3">
              {content.substring(0, 150)}...
            </p>
        </div>
        }

        {/* Stats and Actions */}
        <div className="flex items-center justify-between">
          {/* Author and Stats */}
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <User className="w-3 h-3" />
              <span>{author}</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              <span>{formatDate(updatedDate)}</span>
            </div>
            <div className="flex items-center gap-1">
              <Eye className="w-3 h-3" />
              <span>{views}次阅读</span>
            </div>
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>{calculatedReadTime}分钟</span>
            </div>
            <div className="flex items-center gap-1">
              <ThumbsUp className="w-3 h-3" />
              <span>{likes}个赞</span>
            </div>
          </div>

          {/* Attachments Indicator */}
          {attachments.length > 0 &&
          <div className="flex items-center gap-1 text-xs text-slate-400">
              <File className="w-3 h-3" />
              <span>{attachments.length}个附件</span>
          </div>
          }
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-surface-50/30 border-t border-white/5">
        <div className="flex items-center justify-between">
          {showActions &&
          <div className="flex items-center gap-2">
              <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-xs"
              onClick={(e) => {
                e.stopPropagation();
                // Toggle bookmark
              }}>

                <Bookmark className={`w-4 h-4 mr-1 ${bookmarked ? 'text-amber-500 fill-current' : ''}`} />
                收藏
              </Button>
              <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-xs"
              onClick={(e) => {
                e.stopPropagation();
                // Share article
              }}>

                <Share2 className="w-4 h-4 mr-1" />
                分享
              </Button>
              {attachments.length > 0 &&
            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-xs"
              onClick={(e) => {
                e.stopPropagation();
                // Download attachments
              }}>

                  <Download className="w-4 h-4 mr-1" />
                  下载
            </Button>
            }
          </div>
          }

          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs group-hover:bg-primary/10"
            onClick={(e) => {
              e.stopPropagation();
              onClick?.(article);
            }}>

            查看详情
            <ChevronRight className="w-3 h-3 ml-1 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>
    </motion.div>);

}

// Article Card Tags Component
function ArticleCardTags({ article }) {
  if (!article.tags || article.tags?.length === 0) {return null;}

  return (
    <div className="flex flex-wrap gap-1 mb-3">
      {article.tags.slice(0, 3).map((tag, index) =>
      <Badge key={index} variant="secondary" className="text-xs">
          #{tag}
      </Badge>
      )}
      {article.tags?.length > 3 &&
      <Badge variant="secondary" className="text-xs">
          +{article.tags?.length - 3}
      </Badge>
      }
    </div>);

}
