import BrainViewer from "./BrainViewer";
import "./ResultsView.css";

{/* Center column: the 3D viewer */}
function BrainViewerBox({ file, result, treatmentResult, layers }) {
    return(
        <div className="glass results__viewer">
            {/* reductionPercent isn't used by the viewer yet; it's for the shrink slider later */}
            <BrainViewer
            file={file}
            maskUrl={
                treatmentResult?.maskUrl ||
                result?.maskUrl
            }
            reductionPercent={treatmentResult?.reductionPercent}
            brainOpacity={layers.brain.visible ? layers.brain.opacity : 0}
            tumorOpacity={layers.tumor.visible ? layers.tumor.opacity : 0}
            />
        </div>
    );
}

export default BrainViewerBox;