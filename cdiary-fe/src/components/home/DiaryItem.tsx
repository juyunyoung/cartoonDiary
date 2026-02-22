import React from 'react';
import { Trash2 } from 'lucide-react';
import { ArtifactSummary } from '../../types';

interface DiaryItemProps {
  art: ArtifactSummary;
  activeJob?: any;
  onDelete: (e: React.MouseEvent, id: string) => void;
  onClick: () => void;
}

export const DiaryItem: React.FC<DiaryItemProps> = React.memo(({ art, activeJob, onDelete, onClick }) => {
  // 디버깅 로그 추가
  if (activeJob) {
    console.log(`[Render Item] Artifact: ${art.artifactId}, Status: ${activeJob.status}, Progress: ${activeJob.progress}%`);
  }

  return (
    <div
      className="flex bg-white dark:bg-gray-800 rounded-lg shadow cursor-pointer overflow-hidden border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow h-24"
      onClick={onClick}
    >
      {/* Thumbnail */}
      <div className="w-24 bg-secondary/10 dark:bg-gray-700 flex-shrink-0 flex items-center justify-center relative overflow-hidden">
        {(() => {
          // 1. 작업 중이거나 완료되었지만 아직 썸네일이 준비 안 된 경우 진행바 우선 표시
          if (activeJob && (activeJob.status !== "DONE" || !art.thumbnailUrl)) {
            return (
              <div className="flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800 w-full h-full p-2">
                {activeJob.status === "FAILED" ? (
                  <span className="text-[10px] text-red-500 font-bold text-center px-1">Error</span>
                ) : (
                  <>
                    <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mb-1 overflow-hidden">
                      <div
                        className="bg-primary h-1.5 rounded-full transition-all duration-300 pointer-events-none"
                        style={{ width: `${Math.max(10, activeJob.progress || 0)}%` }}
                      ></div>
                    </div>
                    <span className="text-[9px] text-gray-500 font-medium truncate w-full text-center">
                      {activeJob.step || "Generating"}
                    </span>
                  </>
                )}
              </div>
            );
          }

          // 2. 작업이 없거나 완료되어 썸네일이 있는 경우 이미지 표시
          if (art.thumbnailUrl) {
            return (
              <img
                src={art.thumbnailUrl}
                alt="Thumbnail"
                className="w-full h-full object-cover object-top"
              />
            );
          }

          // 3. 썸네일도 없고 작업 정보도 없는 완전 초기 상태 (대기 중)
          return (
            <div className="flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800 w-full h-full p-2">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-1" />
              <span className="text-[10px] text-gray-500 font-medium">Preparing</span>
            </div>
          );
        })()}
      </div>

      {/* Content */}
      <div className="flex-1 p-3 flex flex-col justify-center min-w-0">
        <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-2">
          <span className="font-medium text-gray-700 dark:text-gray-300">{art.date}</span>
          <span className="px-1.5 py-0.5 bg-secondary/20 dark:bg-gray-700 rounded text-[10px] uppercase tracking-wide">{art.stylePreset}</span>
        </div>
        <div className="font-medium truncate text-gray-900 dark:text-white">{art.summary}</div>
      </div>

      <button
        onClick={(e) => onDelete(e, art.artifactId)}
        className="p-3 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
        title="Delete"
      >
        <Trash2 size={20} />
      </button>
    </div>
  );
}, (prev, next) => {
  return prev.art.artifactId === next.art.artifactId &&
    prev.art.thumbnailUrl === next.art.thumbnailUrl &&
    prev.art.summary === next.art.summary &&
    JSON.stringify(prev.activeJob) === JSON.stringify(next.activeJob);
});
