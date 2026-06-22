"""
landmarks.py

Maintains the semantic landmark database.
"""

from .types import Landmark

from .coordinate_transform import distance


class LandmarkDatabase:

    def __init__(self):

        self.landmarks = []

    ######################################################

    def add(

        self,

        label,

        x,

        y,

        confidence

    ):

        for landmark in self.landmarks:

            if landmark.label != label:
                continue

            d = distance(

                x,

                y,

                landmark.x,

                landmark.y

            )

            if d < 1.0:

                landmark.x = (

                    landmark.x *

                    landmark.observations

                    +

                    x

                ) / (

                    landmark.observations + 1

                )

                landmark.y = (

                    landmark.y *

                    landmark.observations

                    +

                    y

                ) / (

                    landmark.observations + 1

                )

                landmark.confidence = max(

                    landmark.confidence,

                    confidence

                )

                landmark.observations += 1

                return

        self.landmarks.append(

            Landmark(

                label,

                x,

                y,

                confidence=confidence

            )

        )

    ######################################################

    def by_label(

        self,

        label

    ):

        return [

            l

            for l in self.landmarks

            if l.label == label

        ]

    ######################################################

    def nearest(

        self,

        x,

        y,

        radius

    ):

        matches = []

        for landmark in self.landmarks:

            d = distance(

                x,

                y,

                landmark.x,

                landmark.y

            )

            if d <= radius:

                matches.append(

                    (

                        d,

                        landmark

                    )

                )

        matches.sort(

            key=lambda x: x[0]

        )

        return matches