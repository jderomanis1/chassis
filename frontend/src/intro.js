// Called once from the document entry point, outside React's render and reconnect paths.
export function startIntro(audio, gestures) {
  audio.volume = 0.35;

  const capture = { capture: true };
  function play() {
    gestures.removeEventListener('click', play, capture);
    gestures.removeEventListener('keydown', play, capture);
    audio.play().catch(error => {
      if (error.name === 'NotAllowedError') {
        gestures.addEventListener('click', play, capture);
        gestures.addEventListener('keydown', play, capture);
      }
    });
  }

  play();
}
