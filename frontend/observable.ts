import { useState, useEffect } from "react";

type Callback<T> = (state: T) => void;

// something neat I came up with - similar to https://github.com/pmndrs/valtio
export class Observable<T> {
  state: T;
  callbacks: Callback<T>[];

  constructor(init: T, onChange: Callback<T> | null = null) {
    this.state = init;
    this.callbacks = onChange ? [onChange] : [];
  }

  // register with react lifecycle
  useState(): [T, (state: T) => void] {
    const [state, setState] = useState<T>(this.state);
    useEffect(() => {
      this.onChange(setState);
      return () => this.deRegister(setState);
    }, []);
    return [state, this.set.bind(this)];
  }

  onChange(cb: Callback<T>) {
    this.callbacks.push(cb);
  }

  deRegister(cb: Callback<T>) {
    this.callbacks.splice(this.callbacks.indexOf(cb), 1);
  }

  set(state: T) {
    this.state = state;
    for (const cb of this.callbacks) {
      cb(state);
    }
  }
}
