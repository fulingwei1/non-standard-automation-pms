import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  Map, Route, Navigation, MapPin, Truck, RefreshCw, Settings, Download } from
'lucide-react';
import { cn } from "../../lib/utils";
import {
  getStatusConfig } from
'@/lib/constants/service';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

const slideIn = {
  hidden: { x: -20, opacity: 0 },
  visible: { x: 0, opacity: 1, transition: { duration: 0.3 } }
};

/**
 * 路线优化算法组件
 */
const RouteAlgorithm = ({ onOptimize, optimizing, algorithm = 'genetic' }) => {
  const algorithms = {
    genetic: { name: '遗传算法', description: '适合大规模配送任务', speed: '中等' },
    greedy: { name: '贪心算法', description: '快速求解次优解', speed: '快' },
    simulated: { name: '模拟退火', description: '避免局部最优', speed: '较慢' },
    nearest: { name: '最近邻', description: '简单易实现', speed: '非常快' }
  };

  const currentAlgorithm = algorithms[algorithm];

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Settings className="w-5 h-5 text-blue-600" />
          路线优化算法
          <Badge className="bg-blue-500">{currentAlgorithm.name}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-slate-600">
          {currentAlgorithm.description} · 速度: {currentAlgorithm.speed}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Button
            variant="outline"
            onClick={() => onOptimize('genetic')}
            disabled={optimizing}
            className={algorithm === 'genetic' ? 'ring-2 ring-blue-500' : ''}>

            遗传算法
          </Button>
          <Button
            variant="outline"
            onClick={() => onOptimize('greedy')}
            disabled={optimizing}
            className={algorithm === 'greedy' ? 'ring-2 ring-blue-500' : ''}>

            贪心算法
          </Button>
          <Button
            variant="outline"
            onClick={() => onOptimize('simulated')}
            disabled={optimizing}
            className={algorithm === 'simulated' ? 'ring-2 ring-blue-500' : ''}>

            模拟退火
          </Button>
          <Button
            variant="outline"
            onClick={() => onOptimize('nearest')}
            disabled={optimizing}
            className={algorithm === 'nearest' ? 'ring-2 ring-blue-500' : ''}>

            最近邻
          </Button>
        </div>
      </CardContent>
    </Card>);

};

/**
 * 路线统计信息组件
 */
const RouteStats = ({ stats }) => {
  const statConfigs = [
  { key: 'total_distance', label: '总距离', unit: 'km', icon: '🛣️' },
  { key: 'total_time', label: '总时间', unit: '小时', icon: '⏰' },
  { key: 'deliveries_count', label: '配送任务', unit: '单', icon: '📦' },
  { key: 'savings', label: '时间节省', unit: '%', icon: '⚡' }];


  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">路线统计</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statConfigs.map((stat) =>
          <div key={stat.key} className="text-center">
              <div className="text-2xl mb-1">{stat.icon}</div>
              <div className="text-2xl font-bold text-blue-600">
                {stats[stat.key] || 0}
              </div>
              <div className="text-sm text-slate-500">
                {stat.label}
              </div>
              <div className="text-xs text-slate-400">
                {stats[stat.key + '_unit'] || stat.unit}
              </div>
          </div>
          )}
        </div>
      </CardContent>
    </Card>);

};

/**
 * 路线节点组件
 */
const RouteNode = ({ node, isActive, onClick }) => {
  const statusConfig = getStatusConfig(node.status);
  const isDelivery = node.type === 'delivery';

  return (
    <motion.div
      variants={slideIn}
      className={cn(
        "p-3 rounded-lg border cursor-pointer transition-all",
        isActive ? "ring-2 ring-blue-500 border-blue-300" : "border-slate-200",
        isDelivery ? "bg-white" : "bg-slate-50"
      )}
      onClick={onClick}>

      <div className="flex items-center gap-2">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm",
          statusConfig.color
        )}>
          {node.order || node.index}
        </div>
        <div className="flex-1">
          <div className="font-medium flex items-center gap-2">
            {isDelivery ?
            <>
                <MapPin className="w-4 h-4 text-slate-500" />
                {node.recipient_name}
            </> :

            <Truck className="w-4 h-4 text-slate-500" />
            }
          </div>
          <div className="text-sm text-slate-500">
            {isDelivery ? node.address : "配送中心"}
          </div>
          {node.estimated_time &&
          <div className="text-xs text-slate-400">
              预计 {new Date(node.estimated_time).toLocaleTimeString()}
          </div>
          }
        </div>
        {node.distance &&
        <div className="text-sm text-slate-500">
            {node.distance} km
        </div>
        }
      </div>
    </motion.div>);

};

/**
 * 路线优化器组件
 *
 * @param {Object} props
 * @param {Array} props.deliveries - 配送任务列表
 * @param {Function} props.onRouteUpdate - 路线更新回调
 * @param {Function} props.onExportRoute - 导出路线回调
 * @param {boolean} props.optimizing - 优化中状态
 * @param {Object} props.currentRoute - 当前路线
 * @param {Object} props.optimizationStats - 优化统计
 */
export const RouteOptimizer = ({
  deliveries = [],
  onRouteUpdate,
  onExportRoute,
  optimizing = false,
  currentRoute,
  optimizationStats = {}
}) => {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('genetic');
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [routeNodes, setRouteNodes] = useState([]);

  useEffect(() => {
    if (currentRoute) {
      // 构建路线节点
      const nodes = [
      {
        type: 'depot',
        name: '配送中心',
        address: currentRoute.depot_address,
        index: 0,
        status: 'COMPLETED'
      }];


      currentRoute.steps.forEach((step, index) => {
        nodes.push({
          type: 'delivery',
          index: index + 1,
          ...step.delivery,
          status: step.status,
          distance: step.distance,
          estimated_time: step.estimated_time,
          order: step.order
        });
      });

      setRouteNodes(nodes);
      if (!selectedRoute) {
        setSelectedRoute(currentRoute);
      }
    }
  }, [currentRoute]);

  const handleOptimize = async (algorithm) => {
    setSelectedAlgorithm(algorithm);
    await onRouteUpdate(deliveries, algorithm);
  };

  const handleNodeClick = (node) => {
    setSelectedRoute({
      ...selectedRoute,
      selectedNode: node
    });
  };

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 算法选择 */}
      <RouteAlgorithm
        onOptimize={handleOptimize}
        optimizing={optimizing}
        algorithm={selectedAlgorithm} />


      {/* 优化进度 */}
      {optimizing &&
      <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-4">
              <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />
              <span className="font-medium">正在优化路线...</span>
            </div>
            <Progress value={75} className="h-2" />
          </CardContent>
      </Card>
      }

      {/* 路线统计 */}
      {optimizationStats && Object.keys(optimizationStats).length > 0 &&
      <RouteStats stats={optimizationStats} />
      }

      {/* 路线展示 */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-base flex items-center gap-2">
              <Route className="w-5 h-5 text-blue-600" />
              优化路线
              {selectedRoute &&
              <Badge className="bg-green-500">已优化</Badge>
              }
            </CardTitle>
            {selectedRoute &&
            <div className="flex gap-2">
                <Button
                variant="outline"
                size="sm"
                onClick={onExportRoute}>

                  <Download className="w-4 h-4 mr-2" />
                  导出路线
                </Button>
            </div>
            }
          </div>
        </CardHeader>
        <CardContent>
          {routeNodes.length > 0 ?
          <div className="space-y-2">
              {routeNodes.map((node, index) =>
            <motion.div
              key={index}
              variants={slideIn}
              initial="hidden"
              animate="visible">

                  <RouteNode
                node={node}
                isActive={selectedRoute?.selectedNode === node}
                onClick={() => handleNodeClick(node)} />

                  {index < routeNodes.length - 1 &&
              <div className="flex items-center justify-center my-2">
                      <Navigation className="w-4 h-4 text-slate-400" />
              </div>
              }
            </motion.div>
            )}
          </div> :

          <div className="py-12 text-center">
              <Map className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-500 mb-2">暂无路线数据</p>
              <p className="text-sm text-slate-400">
                点击优化按钮开始路线优化
              </p>
          </div>
          }
        </CardContent>
      </Card>

      {/* 路线详情 */}
      {selectedRoute?.selectedNode &&
      <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader>
            <CardTitle className="text-base">节点详情</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div>
                <span className="text-sm text-slate-500">节点类型:</span>
                <span className="ml-2 font-medium">
                  {selectedRoute.selectedNode.type === 'delivery' ? '配送点' : '配送中心'}
                </span>
              </div>
              {selectedRoute.selectedNode.type === 'delivery' &&
            <>
                  <div>
                    <span className="text-sm text-slate-500">收货人:</span>
                    <span className="ml-2 font-medium">
                      {selectedRoute.selectedNode.recipient_name}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-slate-500">联系方式:</span>
                    <span className="ml-2">
                      {selectedRoute.selectedNode.recipient_phone}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-slate-500">地址:</span>
                    <span className="ml-2">
                      {selectedRoute.selectedNode.recipient_address}
                    </span>
                  </div>
            </>
            }
              {selectedRoute.selectedNode.distance &&
            <div>
                  <span className="text-sm text-slate-500">距离:</span>
                  <span className="ml-2 font-medium">
                    {selectedRoute.selectedNode.distance} km
                  </span>
            </div>
            }
              {selectedRoute.selectedNode.estimated_time &&
            <div>
                  <span className="text-sm text-slate-500">预计到达:</span>
                  <span className="ml-2 font-medium">
                    {new Date(selectedRoute.selectedNode.estimated_time).toLocaleString()}
                  </span>
            </div>
            }
            </div>
          </CardContent>
      </Card>
      }
    </motion.div>);

};

export default RouteOptimizer;