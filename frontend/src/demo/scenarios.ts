export interface DemoScenario {
    id: string;
    label: string;
    initialMessage: string;
}

export const DEMO_SCENARIOS: DemoScenario[] = [
    {
        id: "ml-engineer",
        label: "ML Engineer",
        initialMessage: "I want to become a Machine Learning Engineer. I love Python, data structures, and I'm interested in neural networks and big data."
    },
    {
        id: "game-dev",
        label: "Game Dev",
        initialMessage: "I'm interested in computer graphics and game development. I like C++ and real-time rendering. I want to build a game engine."
    },
    {
        id: "data-science",
        label: "Data Science",
        initialMessage: "I'm focused on data analysis and statistics. I want to learn about optimization and how to handle large-scale information systems."
    },
    {
        id: "research",
        label: "Research-oriented",
        initialMessage: "I want to follow a research career. I'm interested in formal methods, logic, and advanced algorithms. I prefer theoretical foundations."
    }
];
