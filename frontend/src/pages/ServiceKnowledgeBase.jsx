/**
 * Service Knowledge Base
 * 知识库/FAQ管理 - 客服工程师高级功能
 * 
 * 功能：
 * 1. 知识库文章创建、编辑、查看
 * 2. FAQ问题管理
 * 3. 知识分类管理
 * 4. 搜索和筛选
 * 5. 知识库统计
 * 6. 常用问题快速访问
 */

import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Search, Filter, Eye, Edit, Trash2, BookOpen, HelpCircle,
  FileText, Tag, Star, TrendingUp, Download, RefreshCw, XCircle,
  ChevronRight, Save, Copy, Share2, ThumbsUp, ThumbsDown,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card, CardContent, CardHeader, CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription, DialogBody
} from '../components/ui/dialog'
import { Textarea } from '../components/ui/textarea'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { toast } from '../components/ui/toast'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { serviceApi } from '../services/api'

// Mock data
const mockArticles = [
  {
    id: 1,
    article_no: 'KB-20260106-001',
    title: '设备常见故障排查指南',
    category: '故障处理',
    tags: ['故障排查', '设备维护', '常见问题'],
    content: '本文档详细介绍了设备常见故障的排查方法和解决方案...',
    author: '张工程师',
    view_count: 156,
    like_count: 23,
    helpful_count: 45,
    is_faq: true,
    is_featured: true,
    status: '已发布',
    created_at: '2026-01-06 10:00:00',
    updated_at: '2026-01-06 10:00:00',
  },
  {
    id: 2,
    article_no: 'KB-20260105-002',
    title: '设备操作培训视频',
    category: '操作指南',
    tags: ['操作培训', '视频教程'],
    content: '设备操作培训视频，包含开机、测试流程、日常维护等内容...',
    author: '王工程师',
    view_count: 89,
    like_count: 12,
    helpful_count: 28,
    is_faq: false,
    is_featured: true,
    status: '已发布',
    created_at: '2026-01-05 14:00:00',
    updated_at: '2026-01-05 14:00:00',
  },
  {
    id: 3,
    article_no: 'KB-20260104-003',
    title: '软件更新说明',
    category: '技术文档',
    tags: ['软件更新', '版本说明'],
    content: '最新软件版本更新说明，包含新功能和bug修复...',
    author: '李工程师',
    view_count: 67,
    like_count: 8,
    helpful_count: 15,
    is_faq: false,
    is_featured: false,
    status: '已发布',
    created_at: '2026-01-04 09:00:00',
    updated_at: '2026-01-04 09:00:00',
  },
]

const categoryConfig = {
  '故障处理': { label: '故障处理', color: 'text-red-400', bg: 'bg-red-500/20' },
  '操作指南': { label: '操作指南', color: 'text-blue-400', bg: 'bg-blue-500/20' },
  '技术文档': { label: '技术文档', color: 'text-purple-400', bg: 'bg-purple-500/20' },
  'FAQ': { label: 'FAQ', color: 'text-green-400', bg: 'bg-green-500/20' },
  '其他': { label: '其他', color: 'text-slate-400', bg: 'bg-slate-500/20' },
}

const statusConfig = {
  '草稿': { label: '草稿', color: 'bg-slate-500', textColor: 'text-slate-400' },
  '已发布': { label: '已发布', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  '已归档': { label: '已归档', color: 'bg-slate-600', textColor: 'text-slate-400' },
}

export default function ServiceKnowledgeBase() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [faqFilter, setFaqFilter] = useState('ALL')
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    published: 0,
    faq: 0,
    featured: 0,
    totalViews: 0,
  })

  useEffect(() => {
    loadArticles()
    loadStatistics()
  }, [])

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      'DRAFT': '草稿',
      'PUBLISHED': '已发布',
      'ARCHIVED': '已归档',
    }
    return statusMap[backendStatus] || backendStatus
  }

  const loadArticles = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = {
        page: 1,
        page_size: 100,
      }
      
      if (categoryFilter !== 'ALL') {
        params.category = categoryFilter
      }
      
      if (faqFilter === 'FAQ_ONLY') {
        params.is_faq = true
      } else if (faqFilter === 'NON_FAQ') {
        params.is_faq = false
      }
      
      if (searchQuery) {
        params.keyword = searchQuery
      }
      
      const response = await serviceApi.knowledgeBase.list(params)
      const articlesData = response.data?.items || response.data || []
      
      // Transform backend data to frontend format
      const transformedArticles = articlesData.map(article => ({
        id: article.id,
        article_no: article.article_no || '',
        title: article.title || '',
        content: article.content || '',
        category: article.category || '',
        tags: article.tags || [],
        status: mapBackendStatus(article.status),
        is_faq: article.is_faq || false,
        is_featured: article.is_featured || false,
        view_count: article.view_count || 0,
        author: article.author_name || '',
        created_at: article.created_at || '',
        updated_at: article.updated_at || '',
      }))
      
      setArticles(transformedArticles)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || '加载知识库文章失败')
      setArticles([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [categoryFilter, faqFilter, searchQuery])

  const loadStatistics = useCallback(async () => {
    try {
      const response = await serviceApi.knowledgeBase.statistics()
      const statsData = response.data || {}
      
      setStats({
        total: statsData.total || 0,
        published: statsData.published || 0,
        faq: statsData.faq || 0,
        featured: statsData.featured || 0,
        totalViews: statsData.total_views || 0,
      })
    } catch (err) {
      // Calculate from local articles as fallback
      setStats({
        total: articles.length,
        published: articles.filter(a => a.status === '已发布').length,
        faq: articles.filter(a => a.is_faq).length,
        featured: articles.filter(a => a.is_featured).length,
        totalViews: articles.reduce((sum, a) => sum + a.view_count, 0),
      })
    }
  }, [articles])

  const filteredArticles = useMemo(() => {
    let result = articles

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(article =>
        article.title.toLowerCase().includes(query) ||
        article.content.toLowerCase().includes(query) ||
        article.tags.some(tag => tag.toLowerCase().includes(query)) ||
        article.article_no.toLowerCase().includes(query)
      )
    }

    // Category filter
    if (categoryFilter !== 'ALL') {
      result = result.filter(article => article.category === categoryFilter)
    }

    // FAQ filter
    if (faqFilter === 'FAQ_ONLY') {
      result = result.filter(article => article.is_faq)
    } else if (faqFilter === 'NON_FAQ') {
      result = result.filter(article => !article.is_faq)
    }

    return result.sort((a, b) => {
      // Featured first, then by view count
      if (a.is_featured && !b.is_featured) return -1
      if (!a.is_featured && b.is_featured) return 1
      return b.view_count - a.view_count
    })
  }, [articles, searchQuery, categoryFilter, faqFilter])

  const handleViewDetail = (article) => {
    setSelectedArticle(article)
    setShowDetailDialog(true)
  }

  const handleCreateArticle = async (articleData) => {
    try {
      await serviceApi.knowledgeBase.create(articleData)
      toast.success('知识库文章创建成功')
      setShowCreateDialog(false)
      await loadArticles()
      await loadStatistics()
    } catch (error) {
      toast.error('创建失败: ' + (error.response?.data?.detail || error.message || '请稍后重试'))
    }
  }

  const handleUpdateArticle = async (articleId, articleData) => {
    try {
      await serviceApi.knowledgeBase.update(articleId, articleData)
      toast.success('文章更新成功')
      setShowDetailDialog(false)
      await loadArticles()
      await loadStatistics()
    } catch (error) {
      toast.error('更新失败，请稍后重试')
    }
  }

  const handleDeleteArticle = async (articleId) => {
    if (!confirm('确定要删除这篇文章吗？')) return
    try {
      // TODO: 调用API
      // await knowledgeBaseApi.delete(articleId)
      toast.success('文章删除成功')
      await loadArticles()
      await loadStatistics()
    } catch (error) {
      toast.error('删除失败，请稍后重试')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="知识库管理"
        description="管理和维护知识库文章，提供FAQ和操作指南"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => { loadArticles(); loadStatistics(); toast.success('数据已刷新'); }}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            <Button
              size="sm"
              className="gap-2"
              onClick={() => setShowCreateDialog(true)}
            >
              <Plus className="w-4 h-4" />
              创建文章
            </Button>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4"
        >
          <motion.div variants={fadeIn}>
            <Card className="bg-slate-800/30 border-slate-700">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总文章数</div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-emerald-500/10 border-emerald-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已发布</div>
                <div className="text-2xl font-bold text-emerald-400">{stats.published}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-blue-500/10 border-blue-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">FAQ</div>
                <div className="text-2xl font-bold text-blue-400">{stats.faq}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-yellow-500/10 border-yellow-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">精选</div>
                <div className="text-2xl font-bold text-yellow-400">{stats.featured}</div>
              </CardContent>
            </Card>
          </motion.div>
          <motion.div variants={fadeIn}>
            <Card className="bg-purple-500/10 border-purple-500/20">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总浏览量</div>
                <div className="text-2xl font-bold text-purple-400">{stats.totalViews}</div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>

        {/* Filters */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索文章标题、内容、标签..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-slate-800/50 border-slate-700"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部分类</option>
                    <option value="故障处理">故障处理</option>
                    <option value="操作指南">操作指南</option>
                    <option value="技术文档">技术文档</option>
                    <option value="FAQ">FAQ</option>
                    <option value="其他">其他</option>
                  </select>
                  <select
                    value={faqFilter}
                    onChange={(e) => setFaqFilter(e.target.value)}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-white"
                  >
                    <option value="ALL">全部</option>
                    <option value="FAQ_ONLY">仅FAQ</option>
                    <option value="NON_FAQ">非FAQ</option>
                  </select>
                  {(searchQuery || categoryFilter !== 'ALL' || faqFilter !== 'ALL') && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('')
                        setCategoryFilter('ALL')
                        setFaqFilter('ALL')
                      }}
                      className="gap-2"
                    >
                      <XCircle className="w-4 h-4" />
                      清除
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Article List */}
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-3">
          {loading ? (
            <LoadingCard rows={5} />
          ) : error && articles.length === 0 ? (
            <ErrorMessage error={error} onRetry={loadArticles} />
          ) : filteredArticles.length === 0 ? (
            <EmptyState
              icon={BookOpen}
              title="暂无知识库文章"
              description={
                searchQuery || categoryFilter !== 'ALL' || faqFilter !== 'ALL'
                  ? "当前筛选条件下没有匹配的文章，请尝试调整筛选条件"
                  : "当前没有知识库文章数据"
              }
            />
          ) : (
            filteredArticles.map((article) => {
              const category = categoryConfig[article.category] || categoryConfig['其他']
              const status = statusConfig[article.status] || statusConfig['草稿']

              return (
                <motion.div key={article.id} variants={fadeIn}>
                  <Card className={cn(
                    'hover:bg-slate-800/50 transition-colors',
                    article.is_featured && 'ring-2 ring-yellow-500/30'
                  )}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-3">
                          {/* Header */}
                          <div className="flex items-center gap-3 flex-wrap">
                            {article.is_featured && (
                              <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                            )}
                            <span className="font-mono text-sm text-slate-300">{article.article_no}</span>
                            <Badge className={cn(category.bg, category.color, 'text-xs')}>
                              {category.label}
                            </Badge>
                            {article.is_faq && (
                              <Badge variant="outline" className="text-xs text-blue-400 border-blue-500/30">
                                <HelpCircle className="w-3 h-3 mr-1" />
                                FAQ
                              </Badge>
                            )}
                            <Badge className={cn(status.color, 'text-xs')}>
                              {status.label}
                            </Badge>
                          </div>

                          {/* Content */}
                          <div>
                            <h3 className="text-white font-medium mb-1 cursor-pointer hover:text-primary transition-colors"
                                onClick={() => handleViewDetail(article)}>
                              {article.title}
                            </h3>
                            <p className="text-sm text-slate-300 line-clamp-2">{article.content}</p>
                          </div>

                          {/* Tags and Footer */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 flex-wrap">
                              {article.tags.map((tag, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  <Tag className="w-3 h-3 mr-1" />
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span className="flex items-center gap-1">
                                <Eye className="w-3 h-3" />
                                {article.view_count}
                              </span>
                              <span className="flex items-center gap-1">
                                <ThumbsUp className="w-3 h-3" />
                                {article.like_count}
                              </span>
                              <span className="flex items-center gap-1">
                                <HelpCircle className="w-3 h-3" />
                                {article.helpful_count}
                              </span>
                              <span>作者: {article.author}</span>
                            </div>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewDetail(article)}
                            className="gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            查看
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })
          )}
        </motion.div>
      </div>

      {/* Create Article Dialog */}
      <AnimatePresence>
        {showCreateDialog && (
          <CreateArticleDialog
            onClose={() => setShowCreateDialog(false)}
            onSubmit={handleCreateArticle}
          />
        )}
      </AnimatePresence>

      {/* Detail Dialog */}
      <AnimatePresence>
        {showDetailDialog && selectedArticle && (
          <ArticleDetailDialog
            article={selectedArticle}
            onClose={() => {
              setShowDetailDialog(false)
              setSelectedArticle(null)
            }}
            onUpdate={handleUpdateArticle}
            onDelete={handleDeleteArticle}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

// Create Article Dialog Component
function CreateArticleDialog({ onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    category: '故障处理',
    content: '',
    tags: [],
    is_faq: false,
    is_featured: false,
    status: '草稿',
  })

  const [tagInput, setTagInput] = useState('')

  const handleSubmit = () => {
    if (!formData.title || !formData.content) {
      toast.error('请填写文章标题和内容')
      return
    }
    onSubmit(formData)
  }

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] })
      setTagInput('')
    }
  }

  const handleRemoveTag = (tag) => {
    setFormData({ ...formData, tags: formData.tags.filter(t => t !== tag) })
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>创建知识库文章</DialogTitle>
          <DialogDescription>填写文章信息，系统将自动生成文章编号</DialogDescription>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">文章标题 *</label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="输入文章标题"
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">分类 *</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="故障处理">故障处理</option>
                  <option value="操作指南">操作指南</option>
                  <option value="技术文档">技术文档</option>
                  <option value="FAQ">FAQ</option>
                  <option value="其他">其他</option>
                </select>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-sm text-slate-400 block">文章内容 *</label>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>支持 Markdown 格式</span>
                  <Badge variant="outline" className="text-xs">Markdown</Badge>
                </div>
              </div>
              <div className="relative">
                <Textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  placeholder="输入文章详细内容...&#10;&#10;支持 Markdown 格式：&#10;- 使用 **粗体** 和 *斜体*&#10;- 使用 # 标题&#10;- 使用 - 或 * 创建列表&#10;- 使用 ```代码块```"
                  rows={12}
                  className="bg-slate-800/50 border-slate-700 font-mono text-sm"
                />
                <div className="absolute bottom-2 right-2 text-xs text-slate-500">
                  {formData.content.length} 字符
                </div>
              </div>
              {/* Markdown Preview Toggle */}
              {formData.content && (
                <div className="mt-2">
                  <details className="group">
                    <summary className="cursor-pointer text-xs text-slate-400 hover:text-slate-300">
                      预览 Markdown 渲染效果
                    </summary>
                    <div className="mt-2 p-3 bg-slate-900/50 border border-slate-700 rounded-lg prose prose-invert prose-sm max-w-none">
                      <div 
                        className="text-slate-200 whitespace-pre-wrap"
                        dangerouslySetInnerHTML={{ 
                          __html: formData.content
                            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*(.*?)\*/g, '<em>$1</em>')
                            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
                            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
                            .replace(/^- (.*$)/gim, '<li>$1</li>')
                            .replace(/\n/g, '<br/>')
                        }}
                      />
                    </div>
                  </details>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-1 block">标签</label>
              <div className="flex gap-2">
                <Input
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="输入标签后按回车"
                  className="bg-slate-800/50 border-slate-700"
                />
                <Button variant="outline" size="sm" onClick={handleAddTag}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {tag}
                      <XCircle
                        className="w-3 h-3 ml-1 cursor-pointer"
                        onClick={() => handleRemoveTag(tag)}
                      />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_faq}
                  onChange={(e) => setFormData({ ...formData, is_faq: e.target.checked })}
                  className="w-4 h-4"
                />
                <label className="text-sm text-slate-400">标记为FAQ</label>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => setFormData({ ...formData, is_featured: e.target.checked })}
                  className="w-4 h-4"
                />
                <label className="text-sm text-slate-400">设为精选</label>
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">状态</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                >
                  <option value="草稿">草稿</option>
                  <option value="已发布">已发布</option>
                </select>
              </div>
            </div>
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>取消</Button>
          <Button onClick={handleSubmit}>
            <Save className="w-4 h-4 mr-2" />
            创建文章
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// Article Detail Dialog Component
function ArticleDetailDialog({ article, onClose, onUpdate, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState(article)

  useEffect(() => {
    setFormData(article)
  }, [article])

  const handleSave = () => {
    onUpdate(article.id, formData)
    setIsEditing(false)
  }

  const category = categoryConfig[article.category] || categoryConfig['其他']
  const status = statusConfig[article.status] || statusConfig['草稿']

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {article.is_featured && (
              <Star className="w-5 h-5 text-yellow-400 fill-yellow-400" />
            )}
            <span>{article.title}</span>
            <Badge className={cn(category.bg, category.color, 'text-xs')}>
              {category.label}
            </Badge>
            {article.is_faq && (
              <Badge variant="outline" className="text-xs text-blue-400 border-blue-500/30">
                FAQ
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>知识库文章详情</DialogDescription>
        </DialogHeader>
        <DialogBody>
          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">文章标题</label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="bg-slate-800/50 border-slate-700"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm text-slate-400 block">文章内容</label>
                  <Badge variant="outline" className="text-xs">Markdown</Badge>
                </div>
                <Textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={15}
                  className="bg-slate-800/50 border-slate-700 font-mono text-sm"
                  placeholder="支持 Markdown 格式..."
                />
                {formData.content && (
                  <div className="mt-2 text-xs text-slate-500">
                    {formData.content.length} 字符
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <p className="text-sm text-slate-400 mb-1">文章编号</p>
                <p className="font-mono text-white">{article.article_no}</p>
              </div>

              <div>
                <p className="text-sm text-slate-400 mb-1">文章内容</p>
                <div className="text-white bg-slate-800/50 p-4 rounded-lg whitespace-pre-wrap">
                  {article.content}
                </div>
              </div>

              {article.tags && article.tags.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">标签</p>
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        <Tag className="w-3 h-3 mr-1" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">作者</p>
                  <p className="text-white">{article.author}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">状态</p>
                  <Badge className={cn(status.color, 'text-xs')}>{status.label}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">创建时间</p>
                  <p className="text-white">{article.created_at}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">更新时间</p>
                  <p className="text-white">{article.updated_at}</p>
                </div>
              </div>

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Eye className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">浏览量:</span>
                  <span className="text-white">{article.view_count}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">点赞:</span>
                  <span className="text-white">{article.like_count}</span>
                </div>
                <div className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-400">有用:</span>
                  <span className="text-white">{article.helpful_count}</span>
                </div>
              </div>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          {isEditing ? (
            <>
              <Button variant="outline" onClick={() => setIsEditing(false)}>取消</Button>
              <Button onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                保存
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={() => onDelete(article.id)}>
                <Trash2 className="w-4 h-4 mr-2" />
                删除
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit className="w-4 h-4 mr-2" />
                编辑
              </Button>
              <Button variant="outline" onClick={onClose}>关闭</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

