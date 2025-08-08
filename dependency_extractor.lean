import Lean
import Lean.Data.Json.FromToJson
import Lean.Elab.BuiltinCommand
import Lean.Meta.Basic
import Lean.Message
import Lean.DeclarationRange

-- specify project import here
-- import PFR.Main

open Lean Elab Term Meta Std

def getTypeStr (n : Name) : TermElabM String := do
  let inf ← getConstInfo n
  let t := inf.toConstantVal.type
  let dat ← ppExpr t
  return s!"{dat}"

def getConstType (n : Name) : TermElabM String := do
  let constInfo ← getConstInfo n
  return match constInfo with
    | ConstantInfo.defnInfo _ => "Definition"
    | ConstantInfo.thmInfo _ => "Theorem"
    | ConstantInfo.axiomInfo _ => "Axiom"
    | _ => "Other"

def getConstantBody (n : Name) : TermElabM (Option Expr) := do
  let constInfo ← getConstInfo n
  let constValue := constInfo.value?
  return constValue

def getAllConstsFromConst (n : Name) : TermElabM (Array Name) := do
  let body ← getConstantBody n
  let type ← getConstInfo n
  let type := type.toConstantVal.type
  let consts1 := match body with
    | some body => body.getUsedConstants
    | none => #[]
  let consts2 := type.getUsedConstants
  let res := consts1 ++ consts2
  let set := HashSet.ofArray res
  return set.toArray

structure BFSState :=
  (g : HashMap Name (List Name))
  (outerLayer : List Name)

def getUsedConstantGraph (names : List Name) (depth : Nat) : TermElabM (List (Name × List Name)) := do
  let state ← (List.range depth).foldlM (fun (state : BFSState) (_ : Nat) => do
    let g := state.g
    let outerLayer := state.outerLayer
    let newNodes ← outerLayer.mapM fun name => do
      let consts ← try getAllConstsFromConst name catch _ => pure #[]
      pure (name, consts)
    let g := newNodes.foldl (fun m p => m.insert p.fst p.snd.toList) g
    let newOuterLayer := newNodes.foldl (fun (set : HashSet Name) (node : Name × Array Name) =>
      let set := set.insertMany node.snd;
      set) HashSet.empty
    let newOuterLayer := newOuterLayer.toList.filter (fun n => !(g.contains n))
    return BFSState.mk g newOuterLayer
  )
    (BFSState.mk HashMap.empty names)
  return state.g.toList

def writeJsonToFile (filePath : String) (json : Json) : IO Unit := do
  let jsonString := toString json
  IO.FS.withFile filePath IO.FS.Mode.write fun handle => do
    handle.putStr jsonString

def pairToJson (pair : Name × List Name) (projectPrefix : String) : TermElabM (Option Json) := do
  let nameStr := toString pair.fst
  let constCategoryStr ← try getConstType pair.fst catch _ => return none
  let nameListStr := pair.snd.map toString
  let constTypeStr ← getTypeStr pair.fst
  let moduleOpt ← findModuleOf? pair.fst
  let moduleStr := match moduleOpt with | some m => m.toString | none => ""
  let fileStr := moduleStr.replace "." "/" ++ ".lean"
  if !fileStr.startsWith projectPrefix then return none  -- Filter based on file path prefix
  let rangesOpt ← Lean.findDeclarationRanges? pair.fst
  let (startLine, endLine, startCol, endCol) := match rangesOpt with
    | some ranges => (ranges.range.pos.line, ranges.range.endPos.line, ranges.range.pos.column, ranges.range.endPos.column)
    | none => (0, 0, 0, 0)
  return Json.mkObj [
    ("name", Json.str nameStr),
    ("constCategory", Json.str constCategoryStr),
    ("constType", constTypeStr),
    ("references", Json.arr (nameListStr.map Json.str).toArray),
    ("file", Json.str fileStr),
    ("startLine", Json.num startLine),
    ("endLine", Json.num endLine)
    -- Add startCol/endCol if desired
  ]

def serializeList (l : List (Name × List Name)) (projectPrefix : String) : TermElabM Json := do
  let res ← l.filterMapM fun pair => pairToJson pair projectPrefix
  return Json.arr res.toArray

def extractDependencies (root : Name) (projectPrefix : String) (depth : Nat) : TermElabM Unit := do
  let g ← getUsedConstantGraph [root] depth
  let js ← serializeList g projectPrefix
  writeJsonToFile s!"{root}.json" js

-- uncomment call extractDependencies on the target theorem
-- Example usage for PFR project
-- #eval extractDependencies `PFR_conjecture "PFR/" 100
