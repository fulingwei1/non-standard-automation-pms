import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { useCustomerManagement } from "./hooks";
import {
    CustomerFilters,
    CustomerTable,
    CreateCustomerDialog,
    EditCustomerDialog,
    CustomerDetailDialog,
    Customer360Dialog
} from "./components";

export default function CustomerManagement() {
    const {
        customers,
        loading,
        total,
        page,
        setPage,
        pageSize,
        industries,
        searchKeyword,
        setSearchKeyword,
        filterIndustry,
        setFilterIndustry,
        filterStatus,
        setFilterStatus,
        showCreateDialog,
        setShowCreateDialog,
        showEditDialog,
        setShowEditDialog,
        showDetailDialog,
        setShowDetailDialog,
        show360Dialog,
        setShow360Dialog,
        selectedCustomer,
        editCustomer,
        customer360,
        loading360,
        handleCreate,
        handleUpdate,
        handleDelete,
        handleViewDetail,
        handleView360,
        prepareEdit
    } = useCustomerManagement();

    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <PageHeader
                title="客户管理"
                description="管理系统客户信息，包括创建、编辑、查看等操作。"
                actions={
                    <Button onClick={() => setShowCreateDialog(true)}>
                        <Plus className="mr-2 h-4 w-4" /> 新增客户
                    </Button>
                }
            />

            <motion.div variants={fadeIn}>
                <Card>
                    <CustomerFilters
                        searchKeyword={searchKeyword}
                        setSearchKeyword={setSearchKeyword}
                        filterIndustry={filterIndustry}
                        setFilterIndustry={setFilterIndustry}
                        filterStatus={filterStatus}
                        setFilterStatus={setFilterStatus}
                        industries={industries}
                    />
                    <CardContent>
                        <CustomerTable
                            customers={customers}
                            loading={loading}
                            total={total}
                            page={page}
                            pageSize={pageSize}
                            setPage={setPage}
                            onViewDetail={handleViewDetail}
                            onView360={handleView360}
                            onEdit={prepareEdit}
                            onDelete={handleDelete}
                        />
                    </CardContent>
                </Card>
            </motion.div>

            {/* Dialogs */}
            <CreateCustomerDialog
                open={showCreateDialog}
                onOpenChange={setShowCreateDialog}
                onSubmit={handleCreate}
            />

            <EditCustomerDialog
                open={showEditDialog}
                onOpenChange={setShowEditDialog}
                data={editCustomer}
                onSubmit={handleUpdate}
            />

            <CustomerDetailDialog
                open={showDetailDialog}
                onOpenChange={setShowDetailDialog}
                data={selectedCustomer}
            />

            <Customer360Dialog
                open={show360Dialog}
                onOpenChange={setShow360Dialog}
                data={customer360}
                loading={loading360}
            />
        </motion.div>
    );
}
