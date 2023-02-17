.. mermaid::

    flowchart TD
        A[shot, run] --> root
        R[Reference shot\nReference run] --> root
        V[Version in memory e.g. 3.38.1] --> VOX
        X[XML path e.g. IDSRoot.xml] --> VOX
        VD[Version on disk memory e.g. 3.37.1] --> VOXD
        XD[XML path on disk memory e.g. 3.37.1] --> VOXD
        VOX{Version or XML\nin memory?} --> root
        VOXD{Version or XML\non disk?} --> root
        L[lazy] --> root
        root[IDSRoot] --> LZ{Lazy?}
        LZ -->|True| D[Loop over direct children with a name\nInitialize IDSToplevel with it]
        N[version is handled special here!] --> D
        LZ-->|False| E[Add name to children, nothing else]
        E -->|on getattr| F{attr style?}
        F -->|already initialized| G["return using super()"]
        F -->|No children| H["return []"]
        F -->|key in _children| I["Initialize IDSToplevel with key"]
        I --> T
        D -->|parent, key/name, ids XML element, backend_version, backend_xml_path| T[IDSToplevel init]
        T -->|"call super()"|K[Got parent, name, structure_xml]
        subgraph STRUCT["IDSStructure.__init__"]
            direction TB
            K --> B
            subgraph MIXIN["IDSMixin.__init__"]
                direction TB
            B[Got parent, name, structure_xml] --> J["Set internal vars on self:\n _name, _parent, _coordinates, _last_backend_xml_hash, _backend_name"]
            end
            J -->|For each XML child| M[Append name to _children]
            M --> O{child data_type}
            O -->|structure| P[Initialize childs IDSStructure]
            P -->|recurse, parent->child| K
            O -->|struct_array| Q[Initialize IDSStructArray]
            O -->|else| S["get_coordinates (can be {})"]
            S --> U["create_leaf_container(child name, child data_type, parent, coordinates, var_type=type)"]
            subgraph LEAF["create_leaf_container"]
            U --> W{Depending on\ndata_type}
            W --> Y[Determine ids_type, ndims from DD_TYPES]
            Y --> Z{ndins ==?}
            Z -->|ndins==0| AA["IDSPrimitive(name, ids_type, ndims, **kwargs)"]
            Z -->|ndins!=0 && ids_type==STR| AB["IDSPrimitive(name, ids_type, ndims, **kwargs)"]
            Z -->|ndins!=0 && ids_type!=STR| AC["IDSNumericArray(name, ids_type, ndims, **kwargs)"]
            end
            subgraph NUMERICARRAY["IDSNumericArray.__init__"]
                direction TB
                        AC --> AD["No special init"]

            end
            subgraph PRIMITIVE["IDSPrimitive.__init__"]
                direction TB
                AA --> AE
                AD --> AE
                AB --> AE["Same call signature, same case?"]
                AE -->|"Call super() IDSMixin init"| AF
                subgraph CHILDMIXIN["IDSMixin.__init__"]
                    direction TB
                    AF[Got parent, name, coordinates] --> AG["Set internal vars on self:\n _name, _parent, _coordinates, _last_backend_xml_hash, _backend_name"]
                end
                AG --> AH["Set internal vars on self:\n __value, _ids_type, _var_type, _ndims, _backend_type=None, _backend_ndims = None"]
                AH --> AI(["A child node has been generated\nPass to parent"])
            end
        end
