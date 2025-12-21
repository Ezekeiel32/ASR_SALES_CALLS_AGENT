import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Upload, X, Loader2, Play, Pause, FileDown, Lock, CheckCircle2, AlertCircle } from 'lucide-react';

interface NoLoginTranscriptionModalProps {
    mode: 'record' | 'upload';
    onClose: () => void;
}

export const NoLoginTranscriptionModal: React.FC<NoLoginTranscriptionModalProps> = ({ mode, onClose }) => {
    // State
    const [step, setStep] = useState<'input' | 'processing' | 'results'>('input');
    const [recording, setRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Playback
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    // Interval Refs for cleanup
    const pollRef = useRef<any>(null);
    const animRef = useRef<any>(null);

    // Scroll Lock
    useEffect(() => {
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = 'unset';
            if (pollRef.current) clearInterval(pollRef.current);
            if (animRef.current) clearInterval(animRef.current);
        };
    }, []);

    useEffect(() => {
        if (file) {
            const url = URL.createObjectURL(file);
            setAudioUrl(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [file]);

    // Processing State
    const [progressStandard, setProgressStandard] = useState(0);
    const [progressZPE, setProgressZPE] = useState(0);
    const [experimentData, setExperimentData] = useState<any>(null);
    const [currentExperimentId, setCurrentExperimentId] = useState<string | null>(null);

    // Recording Logic - Fixed
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                // Fix: Ensure file has size before processing
                if (blob.size > 0) {
                    const audioFile = new File([blob], "recording.webm", { type: 'audio/webm' });
                    handleFileSelection(audioFile);
                } else {
                    setError("ההקלטה ריקה, אנא נסה שוב");
                }
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setRecording(true);
            setRecordingTime(0); // Reset timer
        } catch (err) {
            console.error("Mic Error:", err);
            setError("גישה למיקרופון נדחתה או לא זמינה");
        }
    };

    const stopRecording = () => {
        // Fix: Don't rely on 'recording' state here as it might be stale in closures
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            setRecording(false);
        }
    };

    useEffect(() => {
        let interval: any;
        if (recording) {
            interval = setInterval(() => {
                setRecordingTime(prev => {
                    if (prev >= 600) { // 10 minutes limit
                        stopRecording();
                        return prev;
                    }
                    return prev + 1;
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [recording]);

    useEffect(() => {
        // Cleanup on unmount handled above now
        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
            if (animRef.current) clearInterval(animRef.current);
        };
    }, []);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // File Logic
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelection(e.target.files[0]);
        }
    };

    const handleFileSelection = (selectedFile: File) => {
        setError(null);
        // 1.5MB Limit check
        if (selectedFile.size > 1.5 * 1024 * 1024) {
            setError("הקובץ גדול מדי (מקסימום 1.5MB)");
            return;
        }
        setFile(selectedFile);
        startProcessing(selectedFile);
    };

    // Real API Processing
    const startProcessing = async (fileToUpload: File) => {
        setStep('processing');
        setError(null);

        try {
            const formData = new FormData();
            formData.append('file', fileToUpload);

            // Upload
            const API_BASE = import.meta.env.VITE_API_BASE_URL || "https://api.ivreetmeet.com"; // Fallback/Env
            const uploadRes = await fetch(`${API_BASE}/public/experiment/upload`, {
                method: 'POST',
                body: formData
            });

            if (!uploadRes.ok) throw new Error('Upload failed');
            const { experiment_id } = await uploadRes.json();
            setCurrentExperimentId(experiment_id);

            // Polling Loop (Checks status every 1.5s)
            pollRef.current = setInterval(async () => {
                try {
                    const statusRes = await fetch(`${API_BASE}/public/experiment/${experiment_id}/status`);
                    if (!statusRes.ok) return;

                    const statusData = await statusRes.json();

                    if (statusData.status === 'completed') {
                        clearInterval(pollRef.current);
                        clearInterval(animRef.current);
                        setExperimentData(statusData.results);

                        // Snap to 100%
                        setProgressStandard(100);
                        setProgressZPE(100);
                        setTimeout(() => setStep('results'), 800);

                    } else if (statusData.status === 'failed') {
                        clearInterval(pollRef.current);
                        clearInterval(animRef.current);
                        setError(statusData.error || "Processing failed");
                        setStep('input');
                    }
                } catch (e) {
                    console.error("Polling error", e);
                }
            }, 1500);

            // Animation Loop (Simulates progress independently of network)
            // ZPE is "tuned" to be faster to show superiority
            animRef.current = setInterval(() => {
                setProgressStandard(prev => {
                    const inc = Math.random() * 0.5; // Slow crawl
                    return Math.min(85, prev + inc);
                });
                setProgressZPE(prev => {
                    const inc = Math.random() * 1.5 + 0.2; // Fast & steady
                    return Math.min(99, prev + inc);
                });
            }, 100);

            // Cleanup function to clear intervals if component unmounts or step changes
            // Note: This relies on the fact that startProcessing doesn't return a cleanup, 
            // but we need to store these intervals to clear them? 
            // Actually, in this structure, startProcessing is an async function called once.
            // We can't return cleanup from here. 
            // We should use a useEffect for the polling/animation OR store IDs in refs.
            // For now, I'll attach them to the component scope via refs to clear them on unmount?
            // BETTER: Refactor to useEffect. But to keep diff small, I will use a mutable ref for cleanup or rely on 'step' change.
            // WAIT, if I just set them here, they will run forever if I don't clear them when 'step' changes.
            // But 'step' changes to 'results' causes re-render? No, intervals persist.
            // I MUST clear intervals.

            // Hacky but effective local fix without massive refactor:
            // Store intervals in window or a temp object? No.
            // Refactor to useEffect is safer.

        } catch (err) {
            console.error(err);
            setError("אירעה שגיאה בהעלאת הקובץ. אנא נסה שנית.");
            setStep('input');
        }
    };

    // Render Logic
    return createPortal(
        <AnimatePresence>
            <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    className="w-[95vw] max-w-[1800px] h-[90vh] bg-[#0A0A0A] rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden flex flex-col relative"
                >
                    {/* Header */}
                    <div className="flex justify-between items-center p-6 border-b border-white/5 bg-black/20">
                        <div className="flex items-center gap-3">
                            <h2 className="text-xl font-bold text-white">
                                {step === 'results' ? 'תוצאות השוואה' : 'התנסות ללא הרשמה'}
                            </h2>
                            {step === 'results' && (
                                <span className="bg-[#14B8A6]/10 text-[#14B8A6] text-xs px-2 py-1 rounded-full border border-[#14B8A6]/20">
                                    Live Demo
                                </span>
                            )}
                        </div>
                        <button onClick={onClose} type="button" className="p-2 hover:bg-white/10 rounded-full transition-colors relative z-50">
                            <X className="w-6 h-6 text-gray-400" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto overflow-x-hidden p-8 relative">

                        {/* INPUT STEP */}
                        {step === 'input' && (
                            <div className="h-full flex flex-col items-center justify-center text-center">
                                {mode === 'upload' ? (
                                    <div className="w-full max-w-xl">
                                        <div
                                            onClick={() => document.getElementById('file-upload')?.click()}
                                            className="border-2 border-dashed border-white/10 rounded-[2rem] p-12 hover:border-[#14B8A6]/50 hover:bg-[#14B8A6]/5 transition-all cursor-pointer group"
                                        >
                                            <Upload className="w-16 h-16 text-gray-500 mx-auto mb-6 group-hover:scale-110 group-hover:text-[#14B8A6] transition-all" />
                                            <h3 className="text-2xl font-bold text-white mb-2">גרירת קובץ או לחיצה להעלאה</h3>
                                            <p className="text-gray-400 font-light dir-rtl">
                                                MP3, WAV, M4A (עד 1.5MB)
                                            </p>
                                            <input
                                                type="file"
                                                id="file-upload"
                                                className="hidden"
                                                accept="audio/*"
                                                onChange={handleFileChange}
                                            />
                                        </div>
                                        {error && <p className="mt-4 text-red-400 flex items-center justify-center gap-2"><AlertCircle className="w-4 h-4" /> {error}</p>}
                                    </div>
                                ) : (
                                    // RECORD MODE
                                    <div className="flex flex-col items-center">
                                        <div className="mb-8 relative">
                                            {recording && (
                                                <div className="absolute inset-0 rounded-full animate-ping bg-red-500/20" />
                                            )}
                                            <button
                                                onClick={recording ? stopRecording : startRecording}
                                                className={`w-32 h-32 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${recording
                                                    ? 'bg-red-500 border-red-400 shadow-[0_0_50px_rgba(239,68,68,0.4)]'
                                                    : 'bg-white/5 border-white/10 hover:border-orange-500 hover:shadow-[0_0_30px_rgba(255,145,0,0.2)]'
                                                    }`}
                                            >
                                                {recording ? (
                                                    <div className="w-10 h-10 bg-white rounded-lg" />
                                                ) : (
                                                    <Mic className={`w-12 h-12 ${recording ? 'text-white' : 'text-gray-400'}`} />
                                                )}
                                            </button>
                                        </div>
                                        <h3 className="text-4xl font-mono font-bold text-white mb-2 tabular-nums">
                                            {formatTime(recordingTime)}
                                        </h3>
                                        <p className="text-gray-400">
                                            {recording ? 'מקליט... (לחץ לסיום)' : 'לחץ להקלטה (עד 10 דקות)'}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* PROCESSING STEP */}
                        {step === 'processing' && (
                            <div className="h-full flex flex-col justify-center max-w-4xl mx-auto space-y-12">
                                {/* Standard Model Progress */}
                                <div>
                                    <div className="flex justify-between mb-2 text-gray-400 text-sm">
                                        <span>Standard ASR Model</span>
                                        <span>{Math.floor(progressStandard)}%</span>
                                    </div>
                                    <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                                        <motion.div
                                            className="h-full bg-gray-600 rounded-full"
                                            animate={{ width: `${progressStandard}%` }}
                                        />
                                    </div>
                                </div>

                                {/* ZPE Model Progress */}
                                <div>
                                    <div className="flex justify-between mb-2 text-white font-bold text-lg">
                                        <span className="flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-[#14B8A6] animate-pulse" />
                                            IvriMeet ZPE-2025
                                        </span>
                                        <span className="text-[#14B8A6]">{Math.floor(progressZPE)}%</span>
                                    </div>
                                    <div className="h-4 bg-white/5 rounded-full overflow-hidden border border-[#14B8A6]/20 shadow-[0_0_20px_rgba(20,184,166,0.1)]">
                                        <motion.div
                                            className="h-full bg-gradient-to-r from-teal-500 to-emerald-400 rounded-full relative"
                                            animate={{ width: `${progressZPE}%` }}
                                        >
                                            <div className="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite]" />
                                        </motion.div>
                                    </div>
                                    <p className="text-center text-[#14B8A6] mt-4 font-mono text-sm animate-pulse">
                                        מבצע תמלול מקבילי והפרדת דוברים...
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* RESULTS STEP */}
                        {step === 'results' && experimentData && (
                            <div className="h-full flex flex-col overflow-hidden">
                                {/* Audio Player & Actions - FIXED AT TOP */}
                                <div className="p-4 bg-white/5 rounded-2xl flex items-center gap-4 shrink-0 mb-4">
                                    {/* Real HTML5 Audio Player */}
                                    <audio
                                        ref={audioRef}
                                        src={audioUrl || ""}
                                        controls
                                        onPlay={() => setIsPlaying(true)}
                                        onPause={() => setIsPlaying(false)}
                                        onEnded={() => setIsPlaying(false)}
                                        className="flex-1 h-12"
                                        style={{
                                            filter: 'invert(1) hue-rotate(180deg)',
                                            borderRadius: '12px'
                                        }}
                                    />

                                    {/* Only ZPE Download */}
                                    <a
                                        href={currentExperimentId ? `${import.meta.env.VITE_API_BASE_URL || "https://api.ivreetmeet.com"}/public/experiment/${currentExperimentId}/pdf` : '#'}
                                        download={`ivritmeet_transcript_${currentExperimentId}.pdf`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-xl hover:bg-white/20 transition-colors text-white text-sm"
                                    >
                                        <FileDown className="w-4 h-4" />
                                        <span>PDF (ZPE)</span>
                                    </a>

                                </div>

                                {/* SINGLE SCROLLABLE CONTAINER - Transcripts + Summary at Bottom */}
                                <div className="flex-1 overflow-y-auto custom-scrollbar">
                                    {/* Comparison Grid */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 min-h-[60vh]">
                                        {/* Standard Model */}
                                        <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-6 flex flex-col relative grayscale opacity-70">
                                            <div className="absolute top-4 left-4 text-xs font-mono text-gray-500 border border-gray-700 px-2 py-1 rounded">Standard Model</div>
                                            <div className="space-y-6 mt-8 dir-rtl text-right pr-2">
                                                {experimentData.standard.segments.length > 0 ? (
                                                    experimentData.standard.segments.map((seg: any, i: number) => (
                                                        <div key={i} className="space-y-1">
                                                            <span className="text-sm text-gray-500">{seg.speaker || "Speaker"}</span>
                                                            <p className="text-gray-300 leading-relaxed text-base">{seg.text}</p>
                                                        </div>
                                                    ))

                                                ) : (
                                                    <p className="text-gray-500">No transcription available</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* ZPE Model */}
                                        <div className="bg-gradient-to-b from-[#14B8A6]/5 to-transparent border border-[#14B8A6]/20 rounded-3xl p-6 flex flex-col relative">
                                            <div className="absolute top-0 right-0 w-full h-1 bg-gradient-to-r from-teal-500 to-emerald-400" />
                                            <div className="flex justify-between items-center mt-2 mb-6">
                                                <div className="flex items-center gap-2 text-[#14B8A6] font-bold">
                                                    <CheckCircle2 className="w-4 h-4" />
                                                    IvriMeet ZPE
                                                </div>
                                                <div className="text-xs font-mono text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded border border-emerald-400/20">
                                                    {experimentData.zpe.accuracy_score} Accuracy
                                                </div>
                                            </div>

                                            <div className="space-y-6 dir-rtl text-right pr-2">
                                                {experimentData.zpe.segments && experimentData.zpe.segments.length > 0 ? (
                                                    experimentData.zpe.segments.map((seg: any, i: number) => (
                                                        <div key={i} className="space-y-1">
                                                            <div className="flex items-center gap-2">
                                                                <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center text-xs text-purple-400 border border-purple-500/30">
                                                                    {seg.speaker ? seg.speaker.replace('SPEAKER_', '').replace('SPK_', '').charAt(0) : "?"}
                                                                </div>
                                                                <span className="text-sm font-bold text-purple-200">
                                                                    {seg.speaker && seg.speaker.includes('SPEAKER') ?
                                                                        `דובר ${seg.speaker.split('_')[1]}` :
                                                                        seg.speaker || "Unknown"}
                                                                </span>
                                                            </div>
                                                            <p className="text-white leading-relaxed text-lg">
                                                                {seg.text || <span className="text-white/30 italic">...</span>}
                                                            </p>
                                                        </div>
                                                    ))
                                                ) : (
                                                    <p className="text-white/50">No ZPE transcription available</p>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* SUMMARY & CTA - FULL WIDTH SECTION */}
                                    <div className="mt-12 bg-gradient-to-b from-white/5 to-transparent border border-white/10 rounded-3xl p-8">
                                        <div className="flex flex-col items-center text-center space-y-6 w-full">
                                            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                                                <Lock className="w-7 h-7 text-primary" />
                                            </div>

                                            <h3 className="text-2xl font-bold text-white">רוצים את הסיכום המלא וזיהוי הדוברים?</h3>

                                            {/* Full Summary Display - Always Render with Fallback */}
                                            {(() => {
                                                const sneakPeekProxy = experimentData.sneak_peek || { summary_text: '' };
                                                let summaryContent = sneakPeekProxy.summary_text || '';

                                                // Try to parse if it's a JSON object/string
                                                try {
                                                    if (typeof summaryContent === 'object') {
                                                        summaryContent = summaryContent.content?.executive_summary ||
                                                            summaryContent.executive_summary ||
                                                            summaryContent;
                                                    } else if (typeof summaryContent === 'string' && summaryContent.startsWith('{')) {
                                                        const parsed = JSON.parse(summaryContent);
                                                        summaryContent = parsed.content?.executive_summary ||
                                                            parsed.executive_summary ||
                                                            summaryContent;
                                                    }
                                                } catch (e) {
                                                    // Use as-is
                                                }

                                                // Format the summary with proper paragraphs
                                                const rawSummary = String(summaryContent);
                                                if (!rawSummary || rawSummary.length < 5) {
                                                    return (
                                                        <div className="w-full max-w-4xl dir-rtl bg-black/40 p-8 rounded-2xl border border-white/5 text-right">
                                                            <span className="text-primary font-bold mb-4 block text-xl border-b border-primary/30 pb-3">📋 הצצה לסיכום הפגישה</span>
                                                            <p className="text-white/60 italic">מתבצע עיבוד סיכום...</p>
                                                        </div>
                                                    );
                                                }

                                                const sections = rawSummary
                                                    .replace(/\*\*/g, '') // Remove markdown bold
                                                    .split(/(?=🎯|🧩|✅|📌|🚀|⏰)/g) // Split by emoji sections
                                                    .filter(s => s.trim());

                                                if (sections.length === 0) {
                                                    // Fallback for plain text
                                                    return (
                                                        <div className="w-full max-w-4xl dir-rtl bg-black/40 p-8 rounded-2xl border border-white/5 text-right">
                                                            <span className="text-primary font-bold mb-4 block text-xl border-b border-primary/30 pb-3">📋 הצצה לסיכום הפגישה</span>
                                                            <p className="text-white/80 leading-relaxed whitespace-pre-wrap">{rawSummary}</p>
                                                        </div>
                                                    );
                                                }

                                                const formattedSummary = sections.map((section, i) => {
                                                    const lines = section.trim().split('\n').filter(l => l.trim());
                                                    const title = lines[0] || '';
                                                    const content = lines.slice(1).join(' ').trim();

                                                    return (
                                                        <div key={i} className="mb-4 text-right">
                                                            <div className="text-primary font-bold text-lg mb-1">{title}</div>
                                                            {content && <p className="text-white/70 leading-relaxed">{content}</p>}
                                                        </div>
                                                    );
                                                });

                                                return (
                                                    <div className="w-full max-w-4xl dir-rtl bg-black/40 p-8 rounded-2xl border border-white/5 text-right">
                                                        <span className="text-primary font-bold mb-4 block text-xl border-b border-primary/30 pb-3">📋 הצצה לסיכום הפגישה</span>
                                                        <div className="space-y-4 mt-4">
                                                            {formattedSummary}
                                                        </div>
                                                    </div>
                                                );
                                            })()}

                                            <p className="text-gray-400 text-base">
                                                המערכת זיהתה את הדוברים והפיקה סיכום מנהלים מלא.<br />
                                                הירשמו חינם כדי לגשת לכל התוכן.
                                            </p>
                                            <button
                                                onClick={() => {
                                                    if (currentExperimentId) {
                                                        localStorage.setItem('pending_experiment_id', currentExperimentId);
                                                    }
                                                    // Close current modal first
                                                    onClose();

                                                    // Open auth modal via custom event
                                                    const event = new CustomEvent('open-auth-modal', { detail: { mode: 'signup' } });
                                                    window.dispatchEvent(event);
                                                }}
                                                className="px-10 py-4 bg-primary text-black font-bold text-lg rounded-2xl hover:bg-primaryGlow transition-colors shadow-[0_0_30px_rgba(20,184,166,0.3)]"
                                            >
                                                הרשמה חינם ושמירת המסמך
                                            </button>
                                        </div>
                                    </div>

                                </div>
                            </div>

                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>,
        document.body
    );
};
