"""
Data models for a visa request session.
All fields are optional strings so partial state can be held during the wizard.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class CrewMember:
    full_name: str = ""
    passport_number: str = ""
    passport_expiry: str = ""
    cdc_number: str = ""
    cdc_expiry: str = ""
    gender: str = ""
    date_of_birth: str = ""
    rank: str = ""

    def summary(self, index: int) -> str:
        return (
            f"  {index}. *{self.full_name}*\n"
            f"     پاسپورت: `{self.passport_number}` (انقضا: {self.passport_expiry})\n"
            f"     CDC: `{self.cdc_number}` (انقضا: {self.cdc_expiry})\n"
            f"     جنسیت: {self.gender} | تولد: {self.date_of_birth} | سمت: {self.rank}"
        )


@dataclass
class ShipDetails:
    name: str = ""
    owner: str = ""
    imo_number: str = ""
    registration_date: str = ""


@dataclass
class RoutingDetails:
    origin: str = ""
    destination: str = ""


@dataclass
class VisaSession:
    visa_type: str = ""
    ship: ShipDetails = field(default_factory=ShipDetails)
    routing: RoutingDetails = field(default_factory=RoutingDetails)
    crew: List[CrewMember] = field(default_factory=list)
    # Holds the crew member currently being filled in
    current_crew: CrewMember = field(default_factory=CrewMember)

    def add_current_crew(self) -> None:
        """Commit current_crew to the crew list and reset the buffer."""
        self.crew.append(self.current_crew)
        self.current_crew = CrewMember()

    def summary(self) -> str:
        crew_lines = "\n".join(
            m.summary(i + 1) for i, m in enumerate(self.crew)
        )
        return (
            f"📋 *خلاصه درخواست ویزا*\n\n"
            f"🛂 *نوع ویزا:* {self.visa_type}\n\n"
            f"🚢 *اطلاعات کشتی:*\n"
            f"  نام: {self.ship.name}\n"
            f"  مالک: {self.ship.owner}\n"
            f"  IMO: `{self.ship.imo_number}`\n"
            f"  تاریخ ثبت: {self.ship.registration_date}\n\n"
            f"🗺 *مسیر:*\n"
            f"  مبدا: {self.routing.origin}\n"
            f"  مقصد: {self.routing.destination}\n\n"
            f"👥 *خدمه ({len(self.crew)} نفر):*\n"
            f"{crew_lines}"
        )
