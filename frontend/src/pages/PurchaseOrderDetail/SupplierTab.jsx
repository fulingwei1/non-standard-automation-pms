/**
 * Supplier details tab
 */

import { fadeIn, staggerContainer } from "../../lib/animations";

const SupplierTab = ({ po }) => (
  <Card className="bg-slate-800/50 border-slate-700/50">
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-slate-200">
        <Building2 className="w-5 h-5 text-green-400" />
        {"\u4f9b\u5e94\u5546\u8be6\u60c5"}
      </CardTitle>
    </CardHeader>
    <CardContent>
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        <motion.div variants={fadeIn} className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u4f9b\u5e94\u5546\u540d\u79f0"}</p>
            <p className="font-medium text-slate-100">{po.supplier.name}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u4f9b\u5e94\u5546ID"}</p>
            <p className="font-medium text-slate-100">{po.supplier.id}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u8054\u7cfb\u4eba"}</p>
            <p className="font-medium text-slate-100">{po.supplier.contact}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u8054\u7cfb\u7535\u8bdd"}</p>
            <p className="font-medium text-slate-100 flex items-center gap-2">
              <Phone className="w-4 h-4" />
              {po.supplier.phone}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u90ae\u7bb1"}</p>
            <p className="font-medium text-slate-100 flex items-center gap-2">
              <Mail className="w-4 h-4" />
              {po.supplier.email}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u5730\u5740"}</p>
            <p className="font-medium text-slate-100 flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              {po.supplier.address}
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">{"\u4ed8\u6b3e\u6761\u6b3e"}</p>
            <Badge className="bg-slate-700/50 text-slate-300">
              {po.supplier.paymentTerm}
            </Badge>
          </div>
        </motion.div>
      </motion.div>
    </CardContent>
  </Card>
);

export default SupplierTab;
