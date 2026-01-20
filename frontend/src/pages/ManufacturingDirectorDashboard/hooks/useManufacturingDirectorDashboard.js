import { useState, useEffect, useCallback } from "react";
import {
    productionApi,
    shortageApi,
    serviceApi,
    materialApi,
    businessSupportApi
} from "../../../services/api";

export function useManufacturingDirectorDashboard() {
    const [selectedDate, setSelectedDate] = useState("");
    const [selectedTab, setSelectedTab] = useState("overview");
    const [productionStats, setProductionStats] = useState(null);
    const [serviceStats, setServiceStats] = useState(null);
    const [warehouseStats, setWarehouseStats] = useState(null);
    const [shippingStats, setShippingStats] = useState({
        pendingShipments: 0,
        shippedToday: 0,
        onTimeShippingRate: 0,
        inTransit: 0,
        avgShippingTime: 0
    });
    const [pendingApprovals, setPendingApprovals] = useState([]);
    const [workshopCards, setWorkshopCards] = useState([]);
    const [dailyError, setDailyError] = useState(null);
    const [productionDaily, setProductionDaily] = useState(null);
    const [shortageDaily, setShortageDaily] = useState(null);
    const [loadingDaily, setLoadingDaily] = useState(false);

    const loadProductionStats = useCallback(async () => {
        try {
            const response = await productionApi.getStats();
            setProductionStats(response.data || null);
        } catch (error) {
            console.error("加载生产统计失败:", error);
        }
    }, []);

    const loadServiceStats = useCallback(async () => {
        try {
            const response = await serviceApi.getStats();
            setServiceStats(response.data || null);
        } catch (error) {
            console.error("加载服务统计失败:", error);
        }
    }, []);

    const loadWarehouseStats = useCallback(async () => {
        try {
            const response = await materialApi.getStats();
            setWarehouseStats(response.data || null);
        } catch (error) {
            console.error("加载仓储统计失败:", error);
        }
    }, []);

    const loadDailyReports = useCallback(async (date) => {
        setLoadingDaily(true);
        setDailyError(null);
        try {
            const params = date ? { date } : {};
            const [prodRes, shortRes] = await Promise.allSettled([
                productionApi.getDailyReport(params),
                shortageApi.getDailyReport(params)
            ]);

            if (prodRes.status === "fulfilled") {
                setProductionDaily(prodRes.value.data);
            }
            if (shortRes.status === "fulfilled") {
                setShortageDaily(shortRes.value.data);
            }
        } catch (error) {
            console.error("加载日报失败:", error);
            setDailyError("加载日报数据失败");
        } finally {
            setLoadingDaily(false);
        }
    }, []);

    const loadWorkshops = useCallback(async () => {
        try {
            const response = await productionApi.getWorkshops();
            setWorkshopCards(response.data?.items || []);
        } catch (error) {
            console.error("加载车间数据失败:", error);
        }
    }, []);

    const loadApprovals = useCallback(async () => {
        try {
            const response = await businessSupportApi.getPendingApprovals();
            setPendingApprovals(response.data?.items || []);
        } catch (error) {
            console.error("加载待审批事项失败:", error);
        }
    }, []);

    useEffect(() => {
        loadProductionStats();
        loadServiceStats();
        loadWarehouseStats();
        loadWorkshops();
        loadApprovals();
        loadDailyReports(selectedDate);
    }, [selectedDate]);

    const refresh = useCallback(() => {
        loadProductionStats();
        loadServiceStats();
        loadWarehouseStats();
        loadDailyReports(selectedDate);
    }, [selectedDate, loadProductionStats, loadServiceStats, loadWarehouseStats, loadDailyReports]);

    return {
        selectedDate, setSelectedDate,
        selectedTab, setSelectedTab,
        productionStats, serviceStats, warehouseStats, shippingStats,
        pendingApprovals, workshopCards,
        dailyError, productionDaily, shortageDaily, loadingDaily,
        refresh
    };
}
