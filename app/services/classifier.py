import re
SUPPORTED = {
 "elephant":"elephant","cat":"cat","dog":"dog","butterfly":"butterfly","fish":"fish","bird":"bird",
 "flower":"flower","tree":"tree","leaf":"leaf","sun":"sun","cloud":"cloud",
 "alphabet":"alphabet","letter":"alphabet","number":"number","shape":"shapes","shapes":"shapes",
 "science":"science","fruit":"fruit","apple":"fruit","banana":"fruit","orange":"fruit"
}
def classify(prompt: str):
    normalized=re.sub(r"[^a-z0-9 ]"," ",prompt.lower())
    words=set(normalized.split())
    concepts=list(dict.fromkeys(value for key,value in SUPPORTED.items() if key in words))
    concept=concepts[0] if len(concepts)==1 else None
    purpose_hints={
        "coloring_worksheet":("coloring","colouring","worksheet","coloring page","colouring page"),
        "educational_flashcard":("flashcard","flash card","card"),
        "classroom_poster":("classroom poster","learning poster","poster"),
        "official_publication":("publication","official poster","public information")
    }
    matched_purposes=[purpose for purpose,hints in purpose_hints.items() if any(hint in normalized for hint in hints)]
    inferred_purpose=matched_purposes[0] if len(matched_purposes)==1 else None
    ambiguous=len(concepts)>1 or len(matched_purposes)>1
    if len(concepts)>1:
        message=f"This prompt names multiple supported subjects ({', '.join(concepts)}). Please choose one subject."
    elif len(matched_purposes)>1:
        message="This prompt suggests more than one output purpose. Please choose a purpose."
    elif concept is None:
        message="I couldn't match that prompt to a supported local template. Try elephant, cat, dog, butterfly, fish, bird, flower, tree, leaf, sun, cloud, alphabet, number, shapes, science, or fruit."
    elif inferred_purpose is None:
        message="The subject is supported. Choose a purpose to continue, or confirm a suggested purpose."
    else:
        message=None
    return {"normalized_prompt":normalized.strip(),"supported":concept is not None and not ambiguous,
            "detected_concept":concept,"ambiguous":ambiguous,
            "inferred_purpose":inferred_purpose,"requires_confirmation":concept is not None and inferred_purpose is not None,
            "suggested_purposes":["coloring_worksheet","educational_flashcard","classroom_poster","official_publication"] if concept else [],
            "message":message}
