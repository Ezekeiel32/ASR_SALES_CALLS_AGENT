import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { GoogleGenAI, LiveServerMessage, Modality, Blob } from '@google/genai';
import { MicIcon } from './IconComponents';

// Audio Encoding/Decoding Functions (as per guidelines)
function encode(bytes: Uint8Array): string {
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
    return btoa(binary);
}
const createPcmBlob = (data: Float32Array): Blob => ({
  data: encode(new Uint8Array(new Int16Array(data.map(x => x * 32768)).buffer)),
  mimeType: 'audio/pcm;rate=16000',
});

// Audio Visualizer Component
const AudioVisualizer = ({ stream }: { stream: MediaStream | null }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!stream || !canvasRef.current) return;
        const audioContext = new AudioContext();
        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext('2d');
        let animationFrameId: number;

        const draw = () => {
            animationFrameId = requestAnimationFrame(draw);
            analyser.getByteFrequencyData(dataArray);
            if (!canvasCtx) return;
            canvasCtx.fillStyle = '#F9FAFB';
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] / 2;
                canvasCtx.fillStyle = `rgba(20, 184, 166, ${barHeight / 200})`;
                canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        };
        draw();
        return () => {
            cancelAnimationFrame(animationFrameId);
            audioContext.close();
        };
    }, [stream]);

    return <canvas ref={canvasRef} width="600" height="100" style={{ display: 'block', margin: '0 auto' }} />;
};


const LiveMeetingPage: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState('מוכן');
  const [transcriptionLog, setTranscriptionLog] = useState<string[]>([]);
  const currentLineRef = useRef("");
  const sessionPromiseRef = useRef<Promise<any> | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcriptionLog]);


  const cleanup = useCallback(() => {
    console.log('Cleaning up audio resources...');
    sessionPromiseRef.current?.then(session => session.close()).catch(console.error);
    scriptProcessorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    audioContextRef.current?.close();
    streamRef.current?.getTracks().forEach(track => track.stop());

    sessionPromiseRef.current = null;
    scriptProcessorRef.current = null;
    sourceRef.current = null;
    audioContextRef.current = null;
    streamRef.current = null;

    setIsRecording(false);
    setStatus('ההקלטה הסתיימה');
  }, []);

  const startRecording = async () => {
    setIsRecording(true);
    setStatus('מתחבר...');
    setTranscriptionLog([]);
    currentLineRef.current = "";

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY as string });
        audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
        
        sessionPromiseRef.current = ai.live.connect({
            model: 'gemini-2.5-flash-native-audio-preview-09-2025',
            callbacks: {
                onopen: () => {
                    setStatus('מאזין...');
                    if (!audioContextRef.current || !streamRef.current) return;
                    sourceRef.current = audioContextRef.current.createMediaStreamSource(streamRef.current);
                    scriptProcessorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1);
                    scriptProcessorRef.current.onaudioprocess = (e) => {
                        const inputData = e.inputBuffer.getChannelData(0);
                        sessionPromiseRef.current?.then(session => session.sendRealtimeInput({ media: createPcmBlob(inputData) }));
                    };
                    sourceRef.current.connect(scriptProcessorRef.current);
                    scriptProcessorRef.current.connect(audioContextRef.current.destination);
                },
                onmessage: (message: LiveServerMessage) => {
                    if (message.serverContent?.inputTranscription) {
                        const { text } = message.serverContent.inputTranscription;
                        currentLineRef.current += text;
                        // Force a re-render to show partial transcription
                        setTranscriptionLog(prev => [...prev]);
                    }
                    if (message.serverContent?.turnComplete) {
                        if (currentLineRef.current.trim()) {
                            setTranscriptionLog(prev => [...prev, `דובר: ${currentLineRef.current.trim()}`]);
                        }
                        currentLineRef.current = "";
                    }
                },
                onerror: (e) => { setStatus('שגיאת חיבור'); console.error(e); cleanup(); },
                onclose: () => { setStatus('החיבור נסגר'); cleanup(); },
            },
            config: { inputAudioTranscription: {}, responseModalities: [Modality.AUDIO] },
        });
    } catch (err) {
        setStatus('שגיאה בהפעלת המיקרופון');
        console.error(err);
        setIsRecording(false);
    }
  };

  return (
    <div style={{ paddingTop: '80px', textAlign: 'center' }}>
      <h1 style={{ fontSize: '2.25rem', fontWeight: 700 }}>פגישה חיה</h1>
      <p style={{ fontSize: '1.1rem', color: '#4A5568', marginBottom: '2rem' }}>התחל תמלול בזמן אמת. כל מה שתגיד יתומלל כאן.</p>

      <div style={{ backgroundColor: 'white', border: '1px solid #E2E8F0', borderRadius: '12px', padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <motion.button
            onClick={isRecording ? cleanup : startRecording}
            style={recordButtonStyle}
            animate={{ backgroundColor: isRecording ? '#EF4444' : '#14B8A6' }}
            whileTap={{ scale: 0.95 }}
        >
            <MicIcon width={28} height={28} />
        </motion.button>
        <p style={{ fontWeight: 600, marginTop: '1rem' }}>{status}</p>

        {isRecording && <AudioVisualizer stream={streamRef.current} />}

        <div style={transcriptContainerStyle}>
            {transcriptionLog.map((line, i) => <p key={i} style={{ margin: '0 0 1rem 0' }}>{line}</p>)}
            {currentLineRef.current && <p style={{ margin: 0, color: '#6B7280' }}><em>{`דובר: ${currentLineRef.current}`}</em></p>}
             <div ref={transcriptEndRef} />
        </div>
      </div>
    </div>
  );
};


// Styles
const recordButtonStyle: React.CSSProperties = {
  color: 'white', border: 'none', borderRadius: '50%', width: '80px', height: '80px',
  cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center',
  margin: '0 auto', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
};

const transcriptContainerStyle: React.CSSProperties = {
  backgroundColor: '#F9FAFB', border: '1px solid #F3F4F6', borderRadius: '8px',
  minHeight: '200px', maxHeight: '400px', overflowY: 'auto', padding: '1.5rem', marginTop: '2rem',
  textAlign: 'right', lineHeight: 1.6
};

export default LiveMeetingPage;
