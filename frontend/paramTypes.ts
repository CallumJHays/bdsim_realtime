import { Observable } from "./api";

export type ParamVal = number | number[] | string | boolean;

export interface Param<T extends ParamVal = ParamVal> {
  name: string;
  id: number;
  val: T;
}

export interface NumParam<T extends ParamVal = number> extends Param<T> {
  min: T;
  max: T;
  log_scale: boolean;
  step?: number;
}

export interface VecParam extends NumParam<number[]> {
  min: number[];
  max: number[];
}

export interface EnumParam<T extends ParamVal = ParamVal> extends Param<T> {
  oneof: T[];
}

// hyperparams do actually have a value, but we don't use it on the frontend
export interface HyperParam extends Param<null> {
  id: number;
  params: { [attr: string]: Observable<AnyParam> };
  hidden: string[];
}

export type AnyParam =
  | Param<ParamVal>
  | NumParam<number>
  | VecParam
  | EnumParam<ParamVal>
  | HyperParam;
