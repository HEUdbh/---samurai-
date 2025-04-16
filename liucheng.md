graph TD
    classDef startend fill:#F5EBFF,stroke:#BE8FED,stroke-width:2px;
    classDef process fill:#E5F6FF,stroke:#73A6FF,stroke-width:2px;
    classDef decision fill:#FFF6CC,stroke:#FFBC52,stroke-width:2px;

    A([start]):::startend --> B[data preparation and augmentation]:::process
    B --> B1[building a multi-source video dataset]:::process
    B --> B2[filter blur/duplicate frames]:::process
    B --> B3[dynamic enhancement strategy]:::process
    B3 --> B31[occlusion simulation 10 - 60% area coverage]:::process
    B3 --> B32[light perturbation HSV gamut jitter]:::process
    B3 --> B33[motion blur dynamic nucleogenesis]:::process
    B --> B4[20x scale of dataset size]:::process
    B --> B5[covering 90% real-world variation]:::process
    B --> C[model initialization]:::process
    C --> C1[spine network load ImageNet - 21K pre-trained MobileNetV3 weights]:::process
    C --> C2[decoder inherits COCO detection task parameters]:::process
    C --> C3[dynamic sparse training DST pre-frozen 30% low contribution channel]:::process
    C --> D[multi-stage training]:::process