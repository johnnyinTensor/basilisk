/*
Copyright (c) 2016, Autonomous Vehicle Systems Lab, Univeristy of Colorado at Boulder

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

*/
%module inertial3D
%{
   #include "inertial3D.h"
%}

%include "carrays.i"
%include "stdint.i"
%constant void Update_inertial3D(void*, uint64_t, uint64_t);
%ignore Update_inertial3D;
%constant void SelfInit_inertial3D(void*, uint64_t);
%ignore SelfInit_inertial3D;
%constant void CrossInit_inertial3D(void*, uint64_t);
%ignore CrossInit_inertial3D;
%constant void Reset_inertial3D(void*);
%ignore Reset_inertial3D;
%include "inertial3D.h"

// sample Module supportfile to be included in this sub-module
%include "../_GeneralModuleFiles/attGuidOut.h"