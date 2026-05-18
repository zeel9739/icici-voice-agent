import {
  AudioConference,
  ControlBar,
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import styles from "./VoiceRoom.module.css";

interface Props {
  token: string;
  serverUrl: string;
  roomName: string;
  onLeave: () => void;
}

function AgentStatus() {
  const { state, audioTrack } = useVoiceAssistant();
  const connection = useConnectionState();

  const label =
    connection !== ConnectionState.Connected
      ? "Connecting…"
      : state === "speaking"
      ? "🎙️ Priya is speaking"
      : state === "listening"
      ? "👂 Listening to you"
      : state === "thinking"
      ? "💭 Thinking…"
      : "⏳ Waiting";

  return (
    <div className={styles.agentStatus}>
      <div className={`${styles.dot} ${styles[state ?? "idle"]}`} />
      <span>{label}</span>
    </div>
  );
}

export function VoiceRoom({ token, serverUrl, roomName, onLeave }: Props) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onLeave}
      className={styles.room}
    >
      <RoomAudioRenderer />

      <div className={styles.container}>
        <header className={styles.header}>
          <h2>📞 Live Call</h2>
          <span className={styles.roomName}>{roomName}</span>
        </header>

        <div className={styles.body}>
          <AgentStatus />
          <p className={styles.hint}>
            Priya will introduce herself and qualify your interest in ICICI Prudential funds.
            Speak naturally — the call is recorded for quality purposes.
          </p>
        </div>

        <ControlBar
          variation="minimal"
          controls={{ microphone: true, camera: false, screenShare: false, leave: true }}
        />
      </div>
    </LiveKitRoom>
  );
}
