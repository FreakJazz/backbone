from dataclasses import dataclass

from backbone.application.exceptions import ResourceNotFoundException

from domain.repositories.product_repository import IProductRepository


@dataclass
class DeleteProductCommand:
    product_id: str


class DeleteProductCommandHandler:
    def __init__(self, repo: IProductRepository) -> None:
        self._repo = repo

    def handle(self, cmd: DeleteProductCommand) -> str:
        if not self._repo.exists(cmd.product_id):
            raise ResourceNotFoundException("Product", resource_id=cmd.product_id)
        self._repo.delete(cmd.product_id)
        return cmd.product_id
