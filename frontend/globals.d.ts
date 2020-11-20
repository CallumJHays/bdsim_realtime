// experimental API available only in newer browser versions
declare class ResizeObserver {
  constructor(callback: () => void);

  observe(el: HTMLElement): void;
}
