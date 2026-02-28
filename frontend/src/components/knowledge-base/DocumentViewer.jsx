/**
 * Document Viewer Component
 * 文档查看器组件（占位实现，保证页面可运行）
 */

import { Card, Descriptions, Tag, Space, Button, Typography } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import { KNOWLEDGE_TYPES, FILE_TYPES, CATEGORIES, ACCESS_LEVELS, STATUS_OPTIONS } from '@/lib/constants/knowledge';

const { Paragraph, Link, Text } = Typography;

const DocumentViewer = ({ document, onClose }) => {
  if (!document) {return null;}

  const typeConfig = KNOWLEDGE_TYPES[document.type?.toUpperCase()];
  const fileConfig = FILE_TYPES[document.fileType?.toUpperCase()];
  const categoryConfig = CATEGORIES[document.category?.toUpperCase()];
  const accessConfig = ACCESS_LEVELS[document.accessLevel?.toUpperCase()];
  const statusConfig = STATUS_OPTIONS[document.status?.toUpperCase()];

  return (
    <div>
      <Space style={{ marginBottom: 12 }}>
        <Button icon={<CloseOutlined />} onClick={() => onClose?.()}>
          关闭
        </Button>
        {document.fileUrl && (
          <Link href={document.fileUrl} target="_blank" rel="noreferrer">
            打开文件链接
          </Link>
        )}
      </Space>

      <Card>
        <Descriptions column={2} size="small">
          <Descriptions.Item label="类型">
            <Tag color={typeConfig?.color}>{typeConfig?.label || document.type || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="文件类型">
            <Tag>{fileConfig?.label || document.fileType || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="分类">{categoryConfig?.label || document.category || '-'}</Descriptions.Item>
          <Descriptions.Item label="权限">
            <Tag color={accessConfig?.color}>{accessConfig?.label || document.accessLevel || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusConfig?.color}>{statusConfig?.label || document.status || '-'}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="作者">{document.author || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{document.createdAt || '-'}</Descriptions.Item>
          <Descriptions.Item label="更新时间">{document.updatedAt || '-'}</Descriptions.Item>
          <Descriptions.Item label="大小">{document.size || '-'}</Descriptions.Item>
        </Descriptions>

        <Paragraph style={{ marginTop: 12 }}>
          <Text strong>描述：</Text>
          {document.description || '暂无描述'}
        </Paragraph>

        {Array.isArray(document.tags) && document.tags.length > 0 && (
          <Space wrap>
            {document.tags.map((t) => (
              <Tag key={t}>{t}</Tag>
            ))}
          </Space>
        )}
      </Card>
    </div>
  );
};

export default DocumentViewer;

