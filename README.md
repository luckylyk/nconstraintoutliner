# NConstraint Outliner
for Audodesk Maya 2017 (or higher)  
Author: Lionel Brouyère

### Description  
Simple widget who list all nodes 'dynamicConstraint'.  
Features:  
  - shortcuts to manage constraint ncomponents
  - shortcuts to paint the influences vertex maps
  - save the constraint type (comp to comp, transform, ...)
  - change constraint type after creation
  - filter constraints by ncomponent
  - filter constraints by constraint type 
  - auto rename nodes

### Installation  
place the "nconstraintoutliner" folder the into the maya script folder.

| os       | path                                          |
| ------   | ------                                        |
| linux    | ~/< username >/maya                           |
| windows  | \Users\<username>\Documents\maya              |
| mac os x | ~<username>/Library/Preferences/Autodesk/maya |

Ensure that you pick the nconstraintoutliner-master subfolder.


### How to run
```python
import nconstraintoutliner
nconstraintoutliner.launch()
```
