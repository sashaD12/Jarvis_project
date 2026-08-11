interface PywebviewApi {
  quit: () => void;
}

interface PywebviewBridge {
  api: PywebviewApi;
}

interface RiatWindow extends Window {
  pywebview?: PywebviewBridge;
}

export function quitDesktopApp(): void {
  const riatWindow = window as RiatWindow;
  if (riatWindow.pywebview?.api?.quit) {
    riatWindow.pywebview.api.quit();
    return;
  }
  window.close();
}
