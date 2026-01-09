import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '../ui'
import { MessageSquare, FileText, Calendar, Users, CheckCircle2 } from 'lucide-react'
import { formatDate } from '../../lib/utils'
import { projectWorkspaceApi } from '../../services/api'

export default function ProjectMeetingPanel({ projectId }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [meetingData, setMeetingData] = useState(null)

  useEffect(() => {
    fetchMeetingData()
  }, [projectId])

  const fetchMeetingData = async () => {
    try {
      setLoading(true)
      const response = await projectWorkspaceApi.getMeetings(projectId)
      setMeetingData(response.data)
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">加载中...</div>
        </CardContent>
      </Card>
    )
  }

  if (!meetingData) {
    return (
      <Card>
        <CardContent className="p-6 text-center text-gray-500">
          无法加载会议数据
        </CardContent>
      </Card>
    )
  }

  const { meetings, statistics } = meetingData

  return (
    <div className="space-y-6">
      {/* 统计概览 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">会议总数</p>
              <p className="text-2xl font-bold">{statistics.total_meetings}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">已完成</p>
              <p className="text-2xl font-bold text-green-600">
                {statistics.completed_meetings}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">完成率</p>
              <p className="text-2xl font-bold">
                {statistics.completion_rate?.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-sm text-gray-500">行动项</p>
              <p className="text-2xl font-bold">{statistics.total_action_items}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 会议列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            项目会议
          </CardTitle>
        </CardHeader>
        <CardContent>
          {meetings && meetings.length > 0 ? (
            <div className="space-y-2">
              {meetings.map((meeting) => (
                <div
                  key={meeting.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/strategic-meetings/${meeting.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{meeting.meeting_name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline">{meeting.rhythm_level}</Badge>
                        <span className="text-sm text-gray-500">
                          {formatDate(meeting.meeting_date)}
                        </span>
                        <span className="text-sm text-gray-500">
                          {meeting.organizer_name}
                        </span>
                      </div>
                      {meeting.decisions && (
                        <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                          {meeting.decisions}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {meeting.has_minutes && (
                        <Badge variant="secondary">
                          <FileText className="h-3 w-3 mr-1" />
                          有纪要
                        </Badge>
                      )}
                      {meeting.has_decisions && (
                        <Badge variant="secondary">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          有决策
                        </Badge>
                      )}
                      <Badge
                        variant={
                          meeting.status === 'COMPLETED' ? 'default' : 'secondary'
                        }
                      >
                        {meeting.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">暂无会议记录</div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
