# 移动端AI销售助手 - 前端接入指南

## 概述

本指南面向**前端开发团队**，提供移动端AI销售助手的后端API接入方案。

**适用框架**: React Native / Flutter / 原生iOS/Android

---

## 快速开始

### 1. 获取API访问凭证

```javascript
// 登录获取Token
const response = await fetch('https://api.example.com/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'sales_user',
    password: 'password123'
  })
});

const { access_token } = await response.json();
// 保存Token到本地存储
await AsyncStorage.setItem('auth_token', access_token);
```

### 2. 创建API客户端

```javascript
// api/client.js
const API_BASE_URL = 'https://api.example.com/api/v1/presale/mobile';

class PresaleMobileAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async getAuthHeaders() {
    const token = await AsyncStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async chat(question, presaleTicketId = null, context = null) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({
        question,
        presale_ticket_id: presaleTicketId,
        context
      })
    });

    if (!response.ok) {
      throw new Error('AI问答失败');
    }

    return await response.json();
  }

  async voiceQuestion(audioBase64, format = 'mp3', presaleTicketId = null) {
    const response = await fetch(`${this.baseURL}/voice-question`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({
        audio_base64: audioBase64,
        format,
        presale_ticket_id: presaleTicketId
      })
    });

    if (!response.ok) {
      throw new Error('语音提问失败');
    }

    return await response.json();
  }

  async getVisitPreparation(ticketId) {
    const response = await fetch(`${this.baseURL}/visit-preparation/${ticketId}`, {
      headers: await this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取拜访准备清单失败');
    }

    return await response.json();
  }

  async quickEstimate(equipmentDescription, photoBase64 = null, ticketId = null, customerId = null) {
    const response = await fetch(`${this.baseURL}/quick-estimate`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({
        equipment_description: equipmentDescription,
        equipment_photo_base64: photoBase64,
        presale_ticket_id: ticketId,
        customer_id: customerId
      })
    });

    if (!response.ok) {
      throw new Error('快速估价失败');
    }

    return await response.json();
  }

  async createVisitRecord(data) {
    const response = await fetch(`${this.baseURL}/create-visit-record`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('创建拜访记录失败');
    }

    return await response.json();
  }

  async voiceToVisitRecord(audioBase64, presaleTicketId, customerId, visitDate, visitType) {
    const response = await fetch(`${this.baseURL}/voice-to-visit-record`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({
        audio_base64: audioBase64,
        presale_ticket_id: presaleTicketId,
        customer_id: customerId,
        visit_date: visitDate,
        visit_type: visitType
      })
    });

    if (!response.ok) {
      throw new Error('语音转拜访记录失败');
    }

    return await response.json();
  }

  async getVisitHistory(customerId) {
    const response = await fetch(`${this.baseURL}/visit-history/${customerId}`, {
      headers: await this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取拜访历史失败');
    }

    return await response.json();
  }

  async getCustomerSnapshot(customerId) {
    const response = await fetch(`${this.baseURL}/customer-snapshot/${customerId}`, {
      headers: await this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('获取客户快照失败');
    }

    return await response.json();
  }

  async syncOfflineData(dataType, localId, dataPayload) {
    const response = await fetch(`${this.baseURL}/sync-offline-data`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({
        data_type: dataType,
        local_id: localId,
        data_payload: dataPayload
      })
    });

    if (!response.ok) {
      throw new Error('离线数据同步失败');
    }

    return await response.json();
  }
}

export default new PresaleMobileAPI();
```

---

## 功能实现示例

### 1. AI问答界面

```javascript
// screens/ChatScreen.js
import React, { useState } from 'react';
import { View, TextInput, Button, Text, ScrollView } from 'react-native';
import PresaleMobileAPI from '../api/client';

export default function ChatScreen() {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;

    setLoading(true);
    try {
      const result = await PresaleMobileAPI.chat(question);
      
      setChatHistory([
        ...chatHistory,
        { type: 'question', text: question, time: new Date() },
        { 
          type: 'answer', 
          text: result.answer, 
          questionType: result.question_type,
          time: new Date(result.created_at)
        }
      ]);

      setQuestion('');
    } catch (error) {
      alert('AI问答失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      <ScrollView style={{ flex: 1 }}>
        {chatHistory.map((item, index) => (
          <View key={index} style={{
            alignSelf: item.type === 'question' ? 'flex-end' : 'flex-start',
            backgroundColor: item.type === 'question' ? '#007AFF' : '#E5E5EA',
            padding: 12,
            margin: 8,
            borderRadius: 16,
            maxWidth: '80%'
          }}>
            <Text style={{
              color: item.type === 'question' ? 'white' : 'black'
            }}>{item.text}</Text>
          </View>
        ))}
      </ScrollView>

      <View style={{ flexDirection: 'row', padding: 12 }}>
        <TextInput
          value={question}
          onChangeText={setQuestion}
          placeholder="输入问题..."
          style={{ flex: 1, borderWidth: 1, padding: 8, borderRadius: 8 }}
        />
        <Button 
          title={loading ? "..." : "发送"} 
          onPress={handleAsk} 
          disabled={loading}
        />
      </View>
    </View>
  );
}
```

### 2. 语音问答功能

```javascript
// screens/VoiceScreen.js
import React, { useState } from 'react';
import { View, Button, Text } from 'react-native';
import AudioRecorderPlayer from 'react-native-audio-recorder-player';
import PresaleMobileAPI from '../api/client';

const audioRecorderPlayer = new AudioRecorderPlayer();

export default function VoiceScreen() {
  const [recording, setRecording] = useState(false);
  const [result, setResult] = useState(null);

  const startRecording = async () => {
    setRecording(true);
    await audioRecorderPlayer.startRecorder();
  };

  const stopRecording = async () => {
    const path = await audioRecorderPlayer.stopRecorder();
    setRecording(false);

    // 读取音频文件并转换为base64
    const audioBase64 = await RNFS.readFile(path, 'base64');

    // 调用语音问答API
    try {
      const result = await PresaleMobileAPI.voiceQuestion(audioBase64, 'mp3');
      setResult(result);

      // 可选：播放TTS音频
      if (result.audio_url) {
        await audioRecorderPlayer.startPlayer(result.audio_url);
      }
    } catch (error) {
      alert('语音问答失败: ' + error.message);
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Button 
        title={recording ? "停止录音" : "开始录音"}
        onPress={recording ? stopRecording : startRecording}
      />

      {result && (
        <View style={{ marginTop: 20 }}>
          <Text>识别结果: {result.transcription}</Text>
          <Text>AI回答: {result.answer}</Text>
          <Text>响应时间: {result.response_time}ms</Text>
        </View>
      )}
    </View>
  );
}
```

### 3. 拜访准备清单

```javascript
// screens/VisitPreparationScreen.js
import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, ActivityIndicator } from 'react-native';
import PresaleMobileAPI from '../api/client';

export default function VisitPreparationScreen({ route }) {
  const { ticketId } = route.params;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPreparation();
  }, [ticketId]);

  const loadPreparation = async () => {
    try {
      const result = await PresaleMobileAPI.getVisitPreparation(ticketId);
      setData(result);
    } catch (error) {
      alert('加载失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <ActivityIndicator />;
  }

  return (
    <ScrollView style={{ padding: 16 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold' }}>
        {data.customer_name}
      </Text>

      <Section title="客户背景">
        <Text>{data.customer_background}</Text>
      </Section>

      <Section title="推荐话术">
        {data.recommended_scripts.map((script, index) => (
          <Text key={index}>• {script}</Text>
        ))}
      </Section>

      <Section title="注意事项">
        {data.attention_points.map((point, index) => (
          <Text key={index} style={{ color: 'red' }}>⚠️ {point}</Text>
        ))}
      </Section>

      <Section title="技术资料">
        {data.technical_materials.map((material, index) => (
          <TouchableOpacity key={index} onPress={() => openURL(material.url)}>
            <Text style={{ color: 'blue' }}>📄 {material.name}</Text>
          </TouchableOpacity>
        ))}
      </Section>
    </ScrollView>
  );
}

function Section({ title, children }) {
  return (
    <View style={{ marginVertical: 16 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
        {title}
      </Text>
      {children}
    </View>
  );
}
```

### 4. 快速估价（拍照识别）

```javascript
// screens/QuickEstimateScreen.js
import React, { useState } from 'react';
import { View, Button, Image, Text } from 'react-native';
import ImagePicker from 'react-native-image-picker';
import PresaleMobileAPI from '../api/client';

export default function QuickEstimateScreen() {
  const [photo, setPhoto] = useState(null);
  const [result, setResult] = useState(null);

  const takePhoto = () => {
    ImagePicker.launchCamera({ mediaType: 'photo', includeBase64: true }, (response) => {
      if (response.didCancel) return;
      setPhoto(response);
    });
  };

  const estimate = async () => {
    if (!photo) return;

    try {
      const result = await PresaleMobileAPI.quickEstimate(
        '待识别设备',
        photo.base64
      );
      setResult(result);
    } catch (error) {
      alert('估价失败: ' + error.message);
    }
  };

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <Button title="拍照" onPress={takePhoto} />

      {photo && (
        <Image 
          source={{ uri: photo.uri }} 
          style={{ width: 300, height: 300, marginVertical: 16 }}
        />
      )}

      {photo && <Button title="开始估价" onPress={estimate} />}

      {result && (
        <View style={{ marginTop: 16 }}>
          <Text>识别设备: {result.recognized_equipment}</Text>
          <Text>预估成本: ¥{result.estimated_cost.toLocaleString()}</Text>
          <Text style={{ fontSize: 18, fontWeight: 'bold', color: 'green' }}>
            建议报价: ¥{result.price_range_min.toLocaleString()} - ¥{result.price_range_max.toLocaleString()}
          </Text>
          <Text>置信度: {result.confidence_score}%</Text>
        </View>
      )}
    </View>
  );
}
```

### 5. 离线数据同步

```javascript
// utils/offlineSync.js
import AsyncStorage from '@react-native-async-storage/async-storage';
import PresaleMobileAPI from '../api/client';

const OFFLINE_QUEUE_KEY = 'offline_data_queue';

export async function saveOfflineData(dataType, data) {
  const queue = await getOfflineQueue();
  const localId = `offline_${Date.now()}_${Math.random()}`;
  
  queue.push({
    dataType,
    localId,
    dataPayload: data,
    timestamp: new Date().toISOString()
  });

  await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  return localId;
}

export async function syncOfflineData() {
  const queue = await getOfflineQueue();
  
  if (queue.length === 0) {
    return { success: true, synced: 0, failed: 0 };
  }

  let synced = 0;
  let failed = 0;
  const remainingQueue = [];

  for (const item of queue) {
    try {
      await PresaleMobileAPI.syncOfflineData(
        item.dataType,
        item.localId,
        item.dataPayload
      );
      synced++;
    } catch (error) {
      console.error('同步失败:', error);
      remainingQueue.push(item);
      failed++;
    }
  }

  await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remainingQueue));

  return { success: true, synced, failed };
}

async function getOfflineQueue() {
  const data = await AsyncStorage.getItem(OFFLINE_QUEUE_KEY);
  return data ? JSON.parse(data) : [];
}
```

---

## 最佳实践

### 1. 错误处理

```javascript
async function apiCallWithErrorHandling(apiFunc) {
  try {
    return await apiFunc();
  } catch (error) {
    if (error.status === 401) {
      // Token过期，跳转到登录页
      navigation.navigate('Login');
    } else if (error.status === 500) {
      // 服务器错误
      alert('服务器繁忙，请稍后重试');
    } else {
      alert('操作失败: ' + error.message);
    }
    throw error;
  }
}
```

### 2. 加载状态管理

```javascript
const [loading, setLoading] = useState(false);

async function handleAction() {
  setLoading(true);
  try {
    await apiCall();
  } finally {
    setLoading(false);
  }
}
```

### 3. 网络状态检测

```javascript
import NetInfo from '@react-native-community/netinfo';

NetInfo.addEventListener(state => {
  if (state.isConnected) {
    // 恢复在线，同步离线数据
    syncOfflineData();
  } else {
    // 离线模式
    enableOfflineMode();
  }
});
```

---

## 测试建议

### 单元测试

```javascript
// __tests__/api.test.js
import PresaleMobileAPI from '../api/client';

describe('PresaleMobileAPI', () => {
  it('should call chat API', async () => {
    const result = await PresaleMobileAPI.chat('测试问题');
    expect(result).toHaveProperty('answer');
    expect(result).toHaveProperty('question_type');
  });
});
```

### 集成测试

使用 Detox 或 Appium 进行端到端测试。

---

## 性能优化

### 1. 请求缓存

```javascript
const cache = {};

async function cachedRequest(key, apiFunc) {
  if (cache[key] && Date.now() - cache[key].timestamp < 60000) {
    return cache[key].data;
  }

  const data = await apiFunc();
  cache[key] = { data, timestamp: Date.now() };
  return data;
}
```

### 2. 图片压缩

```javascript
import ImageResizer from 'react-native-image-resizer';

async function compressImage(imageUri) {
  const resized = await ImageResizer.createResizedImage(
    imageUri,
    800,  // maxWidth
    800,  // maxHeight
    'JPEG',
    80    // quality
  );
  return resized.uri;
}
```

---

## 常见问题

### Q1: Token过期怎么处理？

A: 使用 refresh token 自动刷新，或提示用户重新登录。

### Q2: 离线时如何操作？

A: 将数据保存到本地队列，恢复在线后自动同步。

### Q3: 音频文件太大怎么办？

A: 使用音频压缩库，或降低采样率。

---

## 联系开发团队

- 后端技术支持: backend@example.com
- 前端技术咨询: frontend@example.com
