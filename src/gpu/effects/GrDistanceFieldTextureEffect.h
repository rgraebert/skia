/*
 * Copyright 2013 Google Inc.
 *
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */

#ifndef GrDistanceFieldTextureEffect_DEFINED
#define GrDistanceFieldTextureEffect_DEFINED

#include "GrEffect.h"
#include "GrVertexEffect.h"

class GrGLDistanceFieldTextureEffect;

/**
 * The output color of this effect is a modulation of the input color and a sample from a
 * distance field texture (using a smoothed step function near 0.5).
 * It allows explicit specification of the filtering and wrap modes (GrTextureParams). The input
 * coords are a custom attribute.
 */
class GrDistanceFieldTextureEffect : public GrVertexEffect {
public:
    static GrEffectRef* Create(GrTexture* tex, const GrTextureParams& para, bool uniformScale) {
        AutoEffectUnref effect(SkNEW_ARGS(GrDistanceFieldTextureEffect, (tex, para, uniformScale)));
        return CreateEffectRef(effect);
    }

    virtual ~GrDistanceFieldTextureEffect() {}

    static const char* Name() { return "DistanceFieldTexture"; }

    virtual void getConstantColorComponents(GrColor* color, uint32_t* validFlags) const SK_OVERRIDE;
    bool isUniformScale() const { return fUniformScale; }

    typedef GrGLDistanceFieldTextureEffect GLEffect;

    virtual const GrBackendEffectFactory& getFactory() const SK_OVERRIDE;

private:
    GrDistanceFieldTextureEffect(GrTexture* texture, const GrTextureParams& params,
                                 bool uniformScale);

    virtual bool onIsEqual(const GrEffect& other) const SK_OVERRIDE;

    GrTextureAccess fTextureAccess;
    bool            fUniformScale;

    GR_DECLARE_EFFECT_TEST;

    typedef GrVertexEffect INHERITED;
};

#endif
