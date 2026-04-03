import { Check, ChevronRight } from "lucide-react";
import { STEPS } from "./constants";

export default function StepNav({ currentStep }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {STEPS.map((step, index) => {
        const StepIcon = step.icon;
        const isActive = currentStep === step.id;
        const isCompleted = currentStep > step.id;

        return (
          <div key={step.id} className="flex items-center">
            <div
              className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 ${
                isActive
                  ? "border-blue-500 bg-blue-500/20 text-blue-400"
                  : isCompleted
                  ? "border-green-500 bg-green-500/20 text-green-400"
                  : "border-gray-600 bg-gray-800 text-gray-500"
              }`}
            >
              {isCompleted ? <Check className="w-6 h-6" /> : <StepIcon className="w-5 h-5" />}
            </div>
            <div className="ml-3 text-left">
              <div className={`text-sm font-medium ${isActive ? "text-white" : "text-gray-400"}`}>
                {step.title}
              </div>
              <div className="text-xs text-gray-500">{step.description}</div>
            </div>
            {index < STEPS.length - 1 && (
              <ChevronRight className="w-5 h-5 mx-4 text-gray-600" />
            )}
          </div>
        );
      })}
    </div>
  );
}
