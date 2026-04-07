/**
 * Order lifecycle timeline card
 */


const TimelineCard = ({ po }) => (
  <Card className="bg-slate-800/50 border-slate-700/50">
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-slate-200">
        <Calendar className="w-5 h-5 text-blue-400" />
        {"\u8ba2\u5355\u751f\u547d\u5468\u671f"}
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="flex justify-between overflow-x-auto py-6 px-2">
        {(po.timeline || []).map((stage, idx) => (
          <TimelineStage
            key={stage.stage}
            stage={stage}
            idx={idx}
            total={po.timeline?.length}
          />
        ))}
      </div>
    </CardContent>
  </Card>
);

export default TimelineCard;
