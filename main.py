from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List
from database.models import Game
from database.database import SessionLocal, engine, Base
from pydantic import conint, BaseModel, ValidationError, validator

Base.metadata.create_all(bind=engine)


app = FastAPI()


class GameOutput(BaseModel):
    id: int
    info: dict


    class Config:
        orm_mode = True


class MoveInput(BaseModel):
    type: str
    position: conint(ge=0, le=8)

    @validator('type')
    def type_is_valid(cls, v):
        if v.lower() not in ("x", "0"):
            raise ValueError(f'invalid type {v}')
        return v.lower()


def check_current_condition(info: dict):
    d = {"diagonal": [[0, 4, 8], [2, 4, 6]], "vertical": [[0,3,6], [1,4,7], [2,5,8]], "horizontal": [[0,1,2], [3,4,5],[6,7,8]]}
    for key, value in d.items():
        for subList in value:
            first = info.get(str(subList[0]))
            if first == "":
                continue;
            isSame = True
            for index in subList:
                if info.get(str(index)) != first:
                    isSame = False
                    break
            if isSame:
                return  {"game": "finished", "winner": first}

    if all(info.values()):
        return {"game": "finished", "winner": "null"}

    return {"game": "in_progress"}




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/start')
def start(db: Session = Depends(get_db)):
    info = {i: "" for i in range(9)}
    game = Game(info=info)
    db.add(game)
    db.commit()
    db.refresh(game)
    return {"game_id": game.id}


@app.post('/move/{game_id}')
def move(game_id: conint(gt=0), data: MoveInput,  db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        raise HTTPException(detail=f"game - {game_id} not found", status_code=400)
    if (game.last_move_was_x and data.type == "x") or (not game.last_move_was_x and data.type == "0"):
        raise HTTPException(detail=f"last move was yours, you can't make the move again", status_code=400)

    if game.info.get(str(data.position)) != '':
        raise HTTPException(detail={"result": "error", "error_code": "invalid_position"}, status_code=400)

    current_positions = game.info

    if not any(current_positions.values()) and data.type == "0":
        raise HTTPException(detail="0 can't start the game", status_code=400)

    current_positions[str(data.position)] = data.type
    game.info = current_positions
    game.last_move_was_x = True if data.type == "x" else False
    db.commit()
    db.refresh(game)
    return {"result": "success"}



@app.get('/check/{game_id}')
def check(game_id: conint(gt=0), db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if game is None:
        raise HTTPException(detail=f"game - {game_id} not found", status_code=400)
    info = game.info
    return check_current_condition(info)


@app.get('/history', response_model=List[GameOutput])
def history(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return games



