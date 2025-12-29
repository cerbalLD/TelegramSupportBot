class Skeleton:
    async def send(self) -> None:
        raise NotImplementedError("Subclasses must implement this method")
    
    async def create_thread(self) -> None:
        raise NotImplementedError("Subclasses must implement this method")

    async def upload_file(self) -> None:
        raise NotImplementedError("Subclasses must implement this method")