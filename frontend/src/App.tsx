import { useState } from "react";
import { LeadDashboard } from "./components/LeadDashboard";
import { VoiceRoom } from "./components/VoiceRoom";
import type { DialResponse } from "./types";

export default function App() {
  const [session, setSession] = useState<DialResponse | null>(null);

  if (session) {
    return (
      <VoiceRoom
        token={session.participant_token}
        serverUrl={session.livekit_url}
        roomName={session.room_name}
        onLeave={() => setSession(null)}
      />
    );
  }

  return <LeadDashboard onDial={setSession} />;
}
