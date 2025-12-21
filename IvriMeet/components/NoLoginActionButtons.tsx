import React from 'react';
import { motion } from 'framer-motion';
import { Mic, Upload, FileAudio, X } from 'lucide-react';
import { NoLoginTranscriptionModal } from './NoLoginTranscriptionModal';

interface ComparisonButtonsProps {
    className?: string;
    singleButton?: 'record' | 'upload'; // Show only one button
}

export const NoLoginActionButtons: React.FC<ComparisonButtonsProps> = ({ className, singleButton }) => {
    const [modalMode, setModalMode] = React.useState<'record' | 'upload' | null>(null);

    const showRecord = !singleButton || singleButton === 'record';
    const showUpload = !singleButton || singleButton === 'upload';

    return (
        <>
            <div className={`flex flex-col md:flex-row gap-6 justify-center items-center ${className}`}>

                {/* Live Recording Button */}
                {showRecord && (
                    <motion.button
                        whileHover={{ scale: 1.05, y: -5 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setModalMode('record')}
                        className="relative group w-72 h-40 rounded-[2rem] bg-white/10 backdrop-blur-md border border-white/20 overflow-hidden shadow-[0_8px_32px_0_rgba(31,38,135,0.37)] hover:bg-white/15 hover:border-orange-500/30 transition-all duration-300"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                        <div className="relative z-10 h-full flex flex-col justify-between p-6">
                            <div className="flex justify-between items-start">
                                <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20 group-hover:scale-110 transition-transform shadow-inner">
                                    <Mic className="w-6 h-6 text-white group-hover:text-orange-300 transition-colors" />
                                </div>
                                <span className="text-xs font-bold text-white/90 bg-white/10 px-3 py-1 rounded-full border border-white/20 backdrop-blur-sm">
                                    10 דקות חינם
                                </span>
                            </div>

                            <div className="text-right">
                                <h3 className="text-xl font-bold text-white mb-1 group-hover:text-orange-200 transition-colors drop-shadow-md">
                                    הקלטה חיה
                                </h3>
                                <p className="text-xs text-gray-200 font-light opacity-80">
                                    התנסות מיידית במודל 2025
                                </p>
                            </div>
                        </div>
                    </motion.button>
                )}

                {/* File Upload Button */}
                {showUpload && (
                    <motion.button
                        whileHover={{ scale: 1.05, y: -5 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => setModalMode('upload')}
                        className="relative group w-72 h-40 rounded-[2rem] bg-white/10 backdrop-blur-md border border-white/20 overflow-hidden shadow-[0_8px_32px_0_rgba(31,38,135,0.37)] hover:bg-white/15 hover:border-teal-500/30 transition-all duration-300"
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-teal-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                        <div className="relative z-10 h-full flex flex-col justify-between p-6">
                            <div className="flex justify-between items-start">
                                <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center border border-white/20 group-hover:scale-110 transition-transform shadow-inner">
                                    <Upload className="w-6 h-6 text-white group-hover:text-teal-300 transition-colors" />
                                </div>
                                <span className="text-xs font-bold text-white/90 bg-white/10 px-3 py-1 rounded-full border border-white/20 backdrop-blur-sm">
                                    עד 1.5MB
                                </span>
                            </div>

                            <div className="text-right">
                                <h3 className="text-xl font-bold text-white mb-1 group-hover:text-teal-200 transition-colors drop-shadow-md">
                                    העלאת קובץ
                                </h3>
                                <p className="text-xs text-gray-200 font-light opacity-80">
                                    השוואה מול מודלים מתחרים
                                </p>
                            </div>
                        </div>
                    </motion.button>
                )}

            </div>

            {/* Modal */}
            {modalMode && (
                <NoLoginTranscriptionModal
                    mode={modalMode}
                    onClose={() => setModalMode(null)}
                />
            )}
        </>
    );
};
